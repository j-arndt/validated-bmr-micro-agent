---
title: BMR Date & Sequence Validator
emoji: 🛡️
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: 4.31.0
app_file: app.py
pinned: true
license: apache-2.0
short_description: 21 CFR Part 11 deterministic batch record date validator
---


<div align="center">

# 🛡️ Validated BMR Micro-Agent
### Batch Record Date & Sequence Validator — v1.0.0

[![Validation](https://img.shields.io/badge/Validation-IQ%2FOQ%2FPQ%20PASS-brightgreen?style=for-the-badge)](./validation_package/)
[![21 CFR Part 11](https://img.shields.io/badge/21%20CFR%20Part%2011-Compliant-blue?style=for-the-badge)](./validation_package/21CFR11_Addendum.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange?style=for-the-badge)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=for-the-badge)](https://python.org)
[![Compute Cost](https://img.shields.io/badge/Compute%20Cost-%240.000001%20%2F%20exec-purple?style=for-the-badge)]()

**A 100% deterministic, cryptographically-hashed, 21 CFR Part 11-compliant micro-agent  
for validating date formats and chronological sequence in electronic Batch Records.**

*No LLMs. No hallucinations. No ambiguity. Just math.*

</div>

---

## What This Agent Does

In pharmaceutical manufacturing, an electronic Batch Record (eBR) is a legal document. Every date entry must:

1. **Conform to ICH Q7 format** — `DD-MMM-YYYY` (e.g., `10-MAY-2026`)
2. **Follow chronological order** — no step can be dated *before* the preceding step (backdating indicator)

A single deviation triggers an FDA data integrity finding. This agent checks both rules deterministically in < 5 milliseconds.

---

## Architecture

```
Input: BMR Text (plain-text / OCR)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  engine.py  (BatchRecordValidator)                          │
│                                                             │
│  PASS 1: Regex extraction → RULE_01_FORMAT (ICH Q7)         │
│          DD-MMM-YYYY strict? Valid calendar date?           │
│                                                             │
│  PASS 2: Chronological scan → RULE_02_SEQUENCE              │
│          Date[N] >= Date[N-1]? Otherwise → backdating FAIL  │
│                                                             │
│  SHA-256 hash of input → tamper-evident anchor              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
Output: Part11AuditTrail (Pydantic v2 JSON)
  ├── execution_id (UUID v4)
  ├── timestamp_utc (ISO 8601)
  ├── input_sha256 (tamper evidence)
  ├── status: PASS | FAIL
  ├── rules_evaluated[] (every finding with evidence)
  ├── summary (format_failures, sequence_failures)
  └── execution_metadata (runtime_ms, peak_ram_mb)
```

**Zero external API calls. Zero ML inference. Zero hallucination surface.**

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/j-arndt/validated-bmr-micro-agent
cd validated-bmr-micro-agent

# 2. Install
pip install -r requirements.txt

# 3. Run engine (CLI)
python engine.py

# 4. Launch Gradio UI
python app.py
# → http://localhost:7860
```

---

## Sample Output

```json
{
  "schema_version": "1.0",
  "agent_name": "BMR-Date-Sequence-Validator",
  "agent_version": "1.0.0",
  "execution_id": "a3f7c12e-...",
  "timestamp_utc": "2026-05-13T16:00:00.000000+00:00",
  "input_sha256": "e3b0c44298fc1c149afb...",
  "status": "FAIL",
  "rules_evaluated": [
    {
      "rule_id": "RULE_01_FORMAT",
      "result": "FAIL",
      "evidence": {
        "location": "Line 3",
        "found_value": "05/11/2026",
        "expected_value": "DD-MMM-YYYY",
        "delta": "Format deviation - expected ICH Q7 standard"
      }
    },
    {
      "rule_id": "RULE_02_SEQUENCE",
      "result": "FAIL",
      "evidence": {
        "location": "Line 5",
        "found_value": "09-MAY-2026 (follows 11-MAY-2026 at Line 4)",
        "expected_value": ">= 11-MAY-2026",
        "delta": "-2 days - chronological break (possible backdating)"
      }
    }
  ],
  "summary": {
    "total_dates_found": 7,
    "format_failures": 2,
    "sequence_failures": 1
  },
  "execution_metadata": {
    "runtime_ms": 2.847,
    "peak_ram_mb": 38.21
  }
}
```

---

## Validation Package

The `/validation_package` folder contains the regulatory trust layer that separates this from a bare script:

| Document | Description | GAMP 5 Phase |
|---|---|---|
| [`IQ_Report.md`](./validation_package/IQ_Report.md) | Installation Qualification — Python version, dep hashes, file integrity | IQ |
| [`OQ_Test_Matrix.csv`](./validation_package/OQ_Test_Matrix.csv) | 1,000 synthetic test cases (4 categories x 250 rows) | OQ |
| [`21CFR11_Addendum.md`](./validation_package/21CFR11_Addendum.md) | Field-by-field FDA Subpart B requirement mapping + ALCOA+ assessment | OQ/PQ |
| [`generate_oq_matrix.py`](./validation_package/generate_oq_matrix.py) | Reproducible OQ matrix generator (deterministic seed) | OQ |

Generate the OQ matrix locally:
```bash
python validation_package/generate_oq_matrix.py
```

---

## OQ Test Categories

| Category | Count | Description |
|---|---|---|
| A — True Negatives | 250 | Valid format + chronological sequences → `PASS` |
| B — Format Errors | 250 | `MM/DD/YYYY`, `D-Mon-YY`, slash separators, etc. → `FAIL` |
| C — Sequence Errors | 250 | Chronological breaks / backdated entries → `FAIL` |
| D — Edge Cases | 250 | Leap years (29-FEB-2024), impossible dates (31-FEB), same-day entries |

---

## Rules Reference

| Rule ID | Name | Standard | Logic |
|---|---|---|---|
| `RULE_01_FORMAT` | Date Format Check | ICH Q7 / 21 CFR Part 11 | Must match `DD-MMM-YYYY` with valid month abbreviation and valid calendar date |
| `RULE_02_SEQUENCE` | Chronological Sequence | GxP Data Integrity / ALCOA+ | Date[N] must be >= Date[N-1]; any reversal is a backdating indicator |

---

## Design Philosophy

> **We do not use probabilistic generative models for deterministic compliance tasks.**

| Concern | LLM Approach | This Agent |
|---|---|---|
| Cost per execution | ~$0.01–$0.10 | ~$0.000001 |
| Hallucination risk | Present | Zero (deterministic) |
| Audit trail | None | Full 21 CFR Part 11 JSON |
| FDA defensibility | Unvalidated | IQ/OQ/PQ documented |
| Latency | 2–30 seconds | < 5 ms |
| Offline capable | No | Yes |

---

## Requirements

```
pydantic==2.7.1
gradio==4.31.0
psutil==5.9.8
```

Python >= 3.10 | No GPU required | Runs on any laptop or air-gapped GxP server

---

## License

Apache 2.0 — see [`LICENSE`](./LICENSE)

---

<div align="center">
Built by <strong>Justin Arndt</strong><br>
18+ years GxP / CSV / QA | GSK background | Validated Micro-Agent Portfolio<br>
<a href="https://github.com/j-arndt">GitHub</a>
</div>
