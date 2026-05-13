"""
app.py — Gradio UI for HuggingFace Spaces
==========================================
Enterprise compliance UI for the BMR-Date-Sequence-Validator.

Deploy to HuggingFace Spaces:
    1. Push this repo to a new Space (SDK = Gradio)
    2. HF Spaces will auto-install requirements.txt and launch demo.launch()

Run locally:
    python app.py
    → opens http://127.0.0.1:7860
"""

import gradio as gr
from engine import BatchRecordValidator

validator = BatchRecordValidator()


# ── Sample inputs ──────────────────────────────────────────────────────────────
SAMPLE_PASS = """Batch Record: BMR-2026-104
Product: Amoxicillin Trihydrate Capsules 500mg
Batch Size: 500,000 units | Lot No: LT-2026-104

Step 1: Raw materials dispensed on 10-MAY-2026.
Step 2: Granulation initiated on 10-MAY-2026.
Step 3: Drying phase completed on 11-MAY-2026.
Step 4: Blending conducted on 11-MAY-2026.
Step 5: Quality sampling performed on 12-MAY-2026.
Step 6: Final packaging completed on 13-MAY-2026.
Step 7: QA release review signed on 14-MAY-2026."""

SAMPLE_FAIL = """Batch Record: BMR-2026-105
Product: Amoxicillin Trihydrate Capsules 500mg
Batch Size: 500,000 units | Lot No: LT-2026-105

Step 1: Raw materials dispensed on 10-MAY-2026.
Step 2: Granulation initiated on 05/11/2026.     ← OPERATOR ENTERED WRONG FORMAT
Step 3: Drying phase completed on 11-MAY-2026.
Step 4: Blending conducted on 09-MAY-2026.       ← BACKDATED / CHRONOLOGICAL BREAK
Step 5: Quality sampling performed on 31-FEB-2026. ← IMPOSSIBLE CALENDAR DATE
Step 6: Final packaging completed on 12-MAY-2026.
Step 7: QA release review signed on 14-MAY-2026."""

# ── Build UI ──────────────────────────────────────────────────────────────────
with gr.Blocks(
    theme=gr.themes.Monochrome(),
    title="BMR Date & Sequence Validator | 21 CFR Part 11",
) as demo:

    gr.Markdown(
        """
# 🛡️ Certified Micro-Agent: Batch Record Date & Sequence Validator
**Agent:** `BMR-Date-Sequence-Validator v1.0.0` &nbsp;|&nbsp;
**Standard:** ICH Q7 / 21 CFR Part 11 &nbsp;|&nbsp;
**Compute Cost:** ~$0.000001 / execution &nbsp;|&nbsp;
**RAM:** < 50 MB
        
[![Validation Status](https://img.shields.io/badge/Validation-IQ%2FOQ%2FPQ%20PASS-brightgreen?style=flat-square)](https://github.com/j-arndt/validated-bmr-micro-agent/tree/main/validation_package)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=flat-square)](https://github.com/j-arndt/validated-bmr-micro-agent/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=flat-square)](https://python.org)

> **Design thesis:** We do not use probabilistic generative models for deterministic compliance tasks.  
> This agent uses pure regex, date arithmetic, and a state machine — backed by a 1,000-case OQ test suite.  
> Every execution produces a cryptographically-hashed, 21 CFR Part 11 audit trail in < 5 ms.
        """
    )

    gr.Markdown("---")

    with gr.Row():
        # ── Left column: input ──────────────────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Input: Electronic Batch Record (Text / OCR)")
            input_box = gr.Textbox(
                lines=18,
                placeholder="Paste or type batch record text here...",
                label="",
                value=SAMPLE_FAIL,
                show_copy_button=True,
            )
            with gr.Row():
                btn_pass = gr.Button(
                    "✅  Load PASSING Example", variant="secondary"
                )
                btn_fail = gr.Button(
                    "❌  Load FAILING Example", variant="stop"
                )
            run_btn = gr.Button(
                "▶  Run Deterministic Audit",
                variant="primary",
                size="lg",
            )

        # ── Right column: output ────────────────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### 📄 Output: 21 CFR Part 11 Audit Trail (JSON)")
            output_box = gr.Code(
                language="json",
                label="",
                lines=26,
            )

    gr.Markdown("---")

    # ── How it works accordion ───────────────────────────────────────────────
    with gr.Accordion("ℹ️  How this agent works", open=False):
        gr.Markdown(
            """
**Two deterministic rules run in sequence:**

| Rule | ID | Logic |
|---|---|---|
| Format Check | `RULE_01_FORMAT` | Every date token must match `DD-MMM-YYYY` (ICH Q7).  Any other format — `MM/DD/YYYY`, `D-Mon-YY`, impossible dates like `31-FEB` — is a `FAIL`. |
| Sequence Check | `RULE_02_SEQUENCE` | Each consecutive step date must be **≥** the preceding date.  Any reversal is a `FAIL` (backdating indicator). |

**Output fields map directly to 21 CFR Part 11 requirements:**
- `execution_id` — unique run identifier (§ 11.10(d))
- `timestamp_utc` — system-generated, human-readable timestamp (§ 11.10(e))
- `input_sha256` — tamper-evident cryptographic hash of the input (§ 11.70)
- `rules_evaluated` — complete, ordered audit trail of every finding (§ 11.10(e))
            """
        )

    # ── Wire buttons ─────────────────────────────────────────────────────────
    btn_pass.click(lambda: SAMPLE_PASS, inputs=None, outputs=input_box)
    btn_fail.click(lambda: SAMPLE_FAIL, inputs=None, outputs=input_box)
    run_btn.click(
        fn=lambda text: validator.run(text),
        inputs=input_box,
        outputs=output_box,
    )

    gr.Markdown(
        """
<div style="text-align:center; color:#666; font-size:0.85em; margin-top:8px;">
Built by <strong>Justin Arndt</strong> — 18+ years GxP / CSV / QA | 
<a href="https://github.com/j-arndt/validated-bmr-micro-agent" target="_blank">GitHub</a>
</div>
        """
    )

if __name__ == "__main__":
    demo.launch()
