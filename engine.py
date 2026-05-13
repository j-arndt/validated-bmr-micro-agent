"""
engine.py — Deterministic Validation Engine
============================================
Core logic for the BMR-Date-Sequence-Validator (v1.0.0).

Design principle:  Zero probabilistic inference.  Every result is a
deterministic function of the input text.  The same input will always
produce the same cryptographically-hashed output — a non-negotiable
requirement for 21 CFR Part 11 / GAMP 5 Category 5 software.

Rules implemented
-----------------
RULE_01_FORMAT   : Every date token must match DD-MMM-YYYY (ICH Q7 standard).
                   Malformed formats (MM/DD/YYYY, D-Mon-YY, etc.) are FAIL.
RULE_02_SEQUENCE : Chronological ordering — each step date must be >= the
                   preceding step date.  Any reversal is a FAIL (backdating
                   indicator).
"""

import re
import hashlib
import time
import psutil
import os
from datetime import datetime
from schemas import (
    Part11AuditTrail,
    RuleEvaluation,
    Evidence,
    Summary,
    ExecutionMetadata,
)


class BatchRecordValidator:
    """
    Stateless, thread-safe validator for electronic Batch Record text.

    Instantiate once and call `.run(text)` for each batch record to validate.
    All state lives inside the returned `Part11AuditTrail` JSON — the validator
    itself holds no mutable state between calls.
    """

    # ── Regex: broad net to catch both valid AND malformed date strings ────────
    # Catches: 10-MAY-2026, 10/05/2026, 10-May-2026, 5-Jun-26, etc.
    _DATE_PATTERN = re.compile(
        r"\b(?:"
        r"\d{1,2}[-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-/]\d{2,4}"
        r"|"
        r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
        r")\b",
        re.IGNORECASE,
    )

    # ── Strict ICH Q7 format: two-digit day, three-letter month, four-digit year
    _STRICT_FORMAT = re.compile(r"^\d{2}-[A-Za-z]{3}-\d{4}$")

    # Valid abbreviated month names (case-insensitive after normalisation)
    _VALID_MONTHS = {
        "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
    }

    def hash_input(self, text: str) -> str:
        """SHA-256 hex digest of the raw input — tamper-evident anchor."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def run(self, bmr_text: str) -> str:
        """
        Validate a batch record text string and return a 21 CFR Part 11
        audit trail as a pretty-printed JSON string.

        Parameters
        ----------
        bmr_text : str
            Raw text (plain-text or OCR output) of the electronic Batch Record.

        Returns
        -------
        str
            JSON representation of `Part11AuditTrail`.
        """
        start_time = time.perf_counter()
        input_hash = self.hash_input(bmr_text)

        lines = bmr_text.split("\n")
        extracted_dates: list[tuple[str, str, datetime]] = []  # (location, normalized, parsed)
        evaluations: list[RuleEvaluation] = []

        # ── PASS 1: Extraction + RULE_01_FORMAT ───────────────────────────────
        for line_num, line in enumerate(lines, start=1):
            matches = self._DATE_PATTERN.findall(line)
            for raw_match in matches:
                location_str = f"Line {line_num}"

                # Check strict DD-MMM-YYYY format
                is_strict_format = bool(self._STRICT_FORMAT.match(raw_match))

                if is_strict_format:
                    normalized = raw_match.upper()
                    month_token = normalized.split("-")[1]

                    if month_token not in self._VALID_MONTHS:
                        # e.g. 10-ZZZ-2026 — passes regex but invalid month
                        evaluations.append(
                            RuleEvaluation(
                                rule_id="RULE_01_FORMAT",
                                result="FAIL",
                                evidence=Evidence(
                                    location=location_str,
                                    found_value=raw_match,
                                    expected_value="DD-MMM-YYYY with valid month abbreviation",
                                    delta=f"Unknown month token: {month_token}",
                                ),
                            )
                        )
                        continue

                    try:
                        parsed_dt = datetime.strptime(normalized, "%d-%b-%Y")
                        extracted_dates.append((location_str, normalized, parsed_dt))
                        evaluations.append(
                            RuleEvaluation(
                                rule_id="RULE_01_FORMAT",
                                result="PASS",
                                evidence=Evidence(
                                    location=location_str,
                                    found_value=normalized,
                                    expected_value="DD-MMM-YYYY",
                                ),
                            )
                        )
                    except ValueError:
                        # Catches calendar impossibilities: 31-FEB-2026, 30-FEB-2024
                        evaluations.append(
                            RuleEvaluation(
                                rule_id="RULE_01_FORMAT",
                                result="FAIL",
                                evidence=Evidence(
                                    location=location_str,
                                    found_value=raw_match.upper(),
                                    expected_value="Valid Calendar Date (DD-MMM-YYYY)",
                                    delta="Impossible calendar date",
                                ),
                            )
                        )
                else:
                    # Format deviation — wrong separator, wrong case, wrong digit count, etc.
                    evaluations.append(
                        RuleEvaluation(
                            rule_id="RULE_01_FORMAT",
                            result="FAIL",
                            evidence=Evidence(
                                location=location_str,
                                found_value=raw_match,
                                expected_value="DD-MMM-YYYY",
                                delta="Format deviation — expected ICH Q7 standard",
                            ),
                        )
                    )

        # ── PASS 2: RULE_02_SEQUENCE (chronological order) ────────────────────
        seq_fails = 0
        for i in range(1, len(extracted_dates)):
            prev_loc, prev_str, prev_dt = extracted_dates[i - 1]
            curr_loc, curr_str, curr_dt = extracted_dates[i]

            delta_days = (curr_dt - prev_dt).days

            if delta_days < 0:
                seq_fails += 1
                evaluations.append(
                    RuleEvaluation(
                        rule_id="RULE_02_SEQUENCE",
                        result="FAIL",
                        evidence=Evidence(
                            location=curr_loc,
                            found_value=f"{curr_str} (follows {prev_str} at {prev_loc})",
                            expected_value=f">= {prev_str}",
                            delta=f"{delta_days} days — chronological break (possible backdating)",
                        ),
                    )
                )
            else:
                evaluations.append(
                    RuleEvaluation(
                        rule_id="RULE_02_SEQUENCE",
                        result="PASS",
                        evidence=Evidence(
                            location=curr_loc,
                            found_value=curr_str,
                            expected_value=f">= {prev_str}",
                            delta=f"+{delta_days} day(s)",
                        ),
                    )
                )

        # ── PASS 3: Compile & return audit trail ──────────────────────────────
        format_fails = sum(
            1
            for e in evaluations
            if e.rule_id == "RULE_01_FORMAT" and e.result == "FAIL"
        )
        total_fails = sum(1 for e in evaluations if e.result == "FAIL")
        overall_status = "FAIL" if total_fails > 0 else "PASS"

        exec_ms = round((time.perf_counter() - start_time) * 1000, 3)
        ram_mb = round(
            psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2
        )

        audit_trail = Part11AuditTrail(
            input_sha256=input_hash,
            status=overall_status,
            rules_evaluated=evaluations,
            summary=Summary(
                total_dates_found=len(extracted_dates) + format_fails,
                format_failures=format_fails,
                sequence_failures=seq_fails,
            ),
            execution_metadata=ExecutionMetadata(
                runtime_ms=exec_ms,
                peak_ram_mb=ram_mb,
            ),
        )

        return audit_trail.model_dump_json(indent=2)


# ── CLI convenience ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = """Batch Record: BMR-2026-104
Step 1: Raw materials dispensed on 10-MAY-2026.
Step 2: Mixing phase initiated on 11-MAY-2026.
Step 3: Quality sampling conducted on 11-MAY-2026.
Step 4: Final packaging completed on 12-MAY-2026."""

    result = BatchRecordValidator().run(text)
    print(result)
