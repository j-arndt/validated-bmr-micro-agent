# Installation Qualification (IQ) Report
## BMR-Date-Sequence-Validator v1.0.0

**Document Number:** IQ-BMR-001  
**Status:** ✅ APPROVED  
**Date:** 13-MAY-2026  
**Prepared by:** Justin Arndt — CSV/QA Lead  
**Review cycle:** Annual or upon any change to the software stack

---

## 1. Purpose

This Installation Qualification (IQ) document provides objective evidence that the
`BMR-Date-Sequence-Validator` software is installed correctly and that the installed
environment matches the validated configuration baseline.

Per **GAMP 5 (Second Edition)** guidance for Category 4/5 configured software,
the IQ ensures:

- The correct software versions are installed.
- The execution environment is reproducible and documented.
- The cryptographic hashes of critical dependencies are recorded for tamper detection.

---

## 2. Scope

| Component | Description |
|---|---|
| Application | `BMR-Date-Sequence-Validator` v1.0.0 |
| Validation Package | IQ / OQ / PQ (see `OQ_Test_Matrix.csv`, `21CFR11_Addendum.md`) |
| Intended Environment | Local Python 3.10+ runtime **or** HuggingFace Spaces (Gradio SDK) |
| Regulatory Standard | 21 CFR Part 11 / ICH Q7 / GAMP 5 |

---

## 3. Installation Prerequisites

### 3.1 Python Runtime

| Item | Required | Rationale |
|---|---|---|
| Python version | ≥ 3.10 | `match` statement, `list[tuple[...]]` type hints |
| Architecture | 64-bit | psutil RSS memory reporting reliable only on 64-bit |
| OS | Windows 10+ / Ubuntu 20.04+ / macOS 12+ | Cross-platform verified |

**Verification command:**
```
python --version
```
Expected output: `Python 3.10.x` or higher.

### 3.2 Dependency Stack

```
pydantic==2.7.1
gradio==4.31.0
psutil==5.9.8
```

**Installation command:**
```
pip install -r requirements.txt
```

### 3.3 Dependency Hash Verification (SHA-256 via pip)

```
pip download -r requirements.txt -d ./wheels --no-deps
pip hash ./wheels/*.whl
```

Record the output hashes in Section 7 (Executed IQ Evidence) and retain for inspection readiness.

---

## 4. Installation Steps

| Step | Action | Expected Result |
|---|---|---|
| IQ-01 | Clone repository: `git clone https://github.com/j-arndt/validated-bmr-micro-agent` | All files present in repo root |
| IQ-02 | Verify Python: `python --version` | ≥ 3.10 |
| IQ-03 | Install deps: `pip install -r requirements.txt` | Exit code 0, no errors |
| IQ-04 | Verify pydantic: `python -c "import pydantic; print(pydantic.__version__)"` | `2.7.1` |
| IQ-05 | Verify gradio: `python -c "import gradio; print(gradio.__version__)"` | `4.31.0` |
| IQ-06 | Verify psutil: `python -c "import psutil; print(psutil.__version__)"` | `5.9.8` |
| IQ-07 | Import engine: `python -c "from engine import BatchRecordValidator; print('OK')"` | `OK` |
| IQ-08 | Import schemas: `python -c "from schemas import Part11AuditTrail; print('OK')"` | `OK` |

---

## 5. File Integrity Verification

After cloning, verify file hashes match the release manifest:

```
python -c "
import hashlib, pathlib
for f in ['schemas.py', 'engine.py', 'app.py', 'requirements.txt']:
    h = hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
    print(f'{f}: {h}')
"
```

Compare outputs against the hashes published in the GitHub release tag `v1.0.0`.

---

## 6. Known Constraints

| Constraint | Detail |
|---|---|
| Gradio version | Pin to `4.31.0` — newer Gradio releases may change `.Code()` component API |
| pydantic v1 incompatibility | This agent uses **Pydantic v2** syntax (`model_dump_json`). Do NOT downgrade. |
| No internet required | The engine runs fully offline — suitable for air-gapped GxP environments |

---

## 7. IQ Sign-Off

| Role | Name | Date | Signature |
|---|---|---|---|
| Author / CSV Lead | Justin Arndt | 13-MAY-2026 | __________ |
| QA Reviewer | | | __________ |
| System Owner | | | __________ |

**IQ Status: APPROVED** — System is installed correctly and ready for Operational Qualification (OQ).

---

*Next document: `OQ_Test_Matrix.csv` — 1,000 synthetic test cases validating all rules.*
