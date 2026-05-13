"""
schemas.py — Part 11 Audit Trail Contract
=========================================
Pydantic v2 schema defining the strict output structure for every execution
of the BMR-Date-Sequence-Validator.  Every field maps directly to a 21 CFR
Part 11 Subpart B data-integrity requirement (see 21CFR11_Addendum.md).
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid


# ──────────────────────────────────────────────────────────────────────────────
# EVIDENCE  — the atomic unit of proof
# ──────────────────────────────────────────────────────────────────────────────
class Evidence(BaseModel):
    """Immutable, human-readable evidence block attached to each rule evaluation."""

    location: str = Field(
        description="Line number or byte offset in the input document"
    )
    found_value: str = Field(
        description="The raw string extracted from the batch record"
    )
    expected_value: str = Field(
        description="The expected format string or sequence requirement"
    )
    delta: Optional[str] = Field(
        None,
        description="Human-readable difference when the finding is a deviation"
    )


# ──────────────────────────────────────────────────────────────────────────────
# RULE EVALUATION  — one rule, one finding
# ──────────────────────────────────────────────────────────────────────────────
class RuleEvaluation(BaseModel):
    """The result of applying a single validation rule to one extracted value."""

    rule_id: str = Field(
        description="Unique rule identifier (e.g. RULE_01_FORMAT, RULE_02_SEQUENCE)"
    )
    result: str = Field(
        pattern="^(PASS|FAIL|ERROR)$",
        description="Deterministic outcome — never ambiguous"
    )
    evidence: Evidence


# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY  — aggregate statistics
# ──────────────────────────────────────────────────────────────────────────────
class Summary(BaseModel):
    """High-level counts for the executive dashboard and CAPA root-cause analysis."""

    total_dates_found: int = Field(
        description="Total date tokens identified (including malformed)"
    )
    format_failures: int = Field(
        description="Count of dates that fail the DD-MMM-YYYY format check"
    )
    sequence_failures: int = Field(
        description="Count of chronological breaks between consecutive step dates"
    )


# ──────────────────────────────────────────────────────────────────────────────
# EXECUTION METADATA  — performance telemetry for the audit log
# ──────────────────────────────────────────────────────────────────────────────
class ExecutionMetadata(BaseModel):
    """Resource consumption proof — demonstrates suitability for high-frequency GxP use."""

    runtime_ms: float = Field(
        description="Wall-clock execution time in milliseconds"
    )
    peak_ram_mb: float = Field(
        description="RSS memory consumed by this process at end of execution (MB)"
    )


# ──────────────────────────────────────────────────────────────────────────────
# PART 11 AUDIT TRAIL  — the top-level deliverable
# ──────────────────────────────────────────────────────────────────────────────
class Part11AuditTrail(BaseModel):
    """
    21 CFR Part 11 compliant audit trail document.

    Every execution of this agent produces exactly one instance of this class.
    The schema is versioned, cryptographically anchored to the input, and fully
    self-describing — suitable for submission to an FDA data-integrity inspection.
    """

    schema_version: str = Field(
        default="1.0",
        description="Schema version for forward-compatibility tracking"
    )
    agent_name: str = Field(
        default="BMR-Date-Sequence-Validator",
        description="Canonical agent identifier"
    )
    agent_version: str = Field(
        default="1.0.0",
        description="Semantic version of the validation engine"
    )
    execution_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID v4 — unique identifier for this specific execution run"
    )
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp in UTC — satisfies 21 CFR 11.10(e) time-stamp requirement"
    )
    input_sha256: str = Field(
        ...,
        description="SHA-256 hex digest of the input text — tamper-evident anchor per 21 CFR 11.70"
    )
    status: str = Field(
        pattern="^(PASS|FAIL)$",
        description="Overall execution outcome — PASS only if every rule evaluation is PASS"
    )
    rules_evaluated: List[RuleEvaluation] = Field(
        description="Ordered list of every rule application and its evidence"
    )
    summary: Summary
    execution_metadata: ExecutionMetadata
