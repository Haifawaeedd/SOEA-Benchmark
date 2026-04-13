# SOEA-Plus: Beyond Accuracy — The Control Collapse Gap in Metacognitive Evaluation of LLMs

[![Kaggle Competition](https://img.shields.io/badge/Kaggle-Measuring%20AGI-blue)](https://www.kaggle.com/competitions/kaggle-measuring-agi)
[![Track](https://img.shields.io/badge/Track-Metacognition-green)](https://www.kaggle.com/competitions/kaggle-measuring-agi)
[![Dataset](https://img.shields.io/badge/Dataset-1%2C676%20PubMed%20Pairs-orange)](https://pubmed.ncbi.nlm.nih.gov/)
[![Models](https://img.shields.io/badge/Models-GPT--4.1%20%7C%20Gemini--2.5%20%7C%20Llama--4-red)](https://openai.com/)

---

## Overview

**SOEA-Plus** (Second-Order Error Awareness) is a benchmark designed to evaluate the **metacognitive capabilities** of Large Language Models (LLMs) — specifically, whether models can not only detect their own uncertainty, but also act safely upon it.

> **Core Research Question:** *Does a model's ability to monitor its own uncertainty guarantee its ability to execute safe control decisions?*

Our answer, backed by experiments on 1,676 real PubMed claim-evidence pairs and 4 frontier models, is: **No.** We identify and quantify a systemic failure pattern we call the **Control Collapse Gap**.

---

## Key Findings

| Model | Accuracy | SOCE | Control Rationality | PDEMC | AUR |
|---|---|---|---|---|---|
| *Human Baseline* | *91.0%* | *-0.018* | *88.3%* | *0.929* | *6.2%* |
| GPT-4.1 | 86.7% | +0.072 | 61.7% | 0.682 | 26.5% |
| GPT-4.1-mini | 80.0% | +0.181 | 48.3% | 0.561 | **55.4%** |
| Gemini-2.5-Flash | 84.0% | -0.012 | 73.3% | **0.756** | 30.3% |
| Llama-4-Scout | 60.3% | +0.376 | 14.0% | 0.470 | 0.0% |

**GPT-4.1-mini exhibits a +31.7% Control Collapse Gap** (80.0% accuracy vs. 48.3% control rationality).

---

## The Three-Stage Evaluation Protocol

```
Stage 1: Prediction (Decision)
    → Model predicts SUPPORTED / INCONCLUSIVE / REFUTED

Stage 2: Confidence (Monitoring)
    → Model assigns confidence score [0, 1]

Stage 3: Adaptive Control
    → Model chooses: COMMIT / REVISE / ABSTAIN / SEEK_EVIDENCE
    
    ⚠️ No new evidence is introduced between Stage 2 and Stage 3.
    This ensures Stage 3 reflects pure metacognitive regulation.
```

---

## Metrics

### SOCE (Second-Order Calibration Error)
```
SOCE = E[conf | incorrect] - E[conf | correct]
```
Positive SOCE = overconfidence when wrong. Unlike ECE, SOCE captures directional failure.

### PDEMC (Post-Decision Error-sensitive Metacognitive Control)
```
PDEMC = 0.4 × Acc + 0.3 × (1 - SOCE_norm) + 0.3 × CR
```
A composite score integrating accuracy, monitoring fidelity, and control rationality.

### REO (Reverse Epistemic Ordering)
```
REO = P(conf_incorrect > conf_correct)
```
GPT-4.1-mini REO = 0.8263 — confidence is epistemically inverted.

### AUR (Aware-but-Unsafe Rate)
```
AUR = P(action=COMMIT | confidence < τ)
```
GPT-4.1-mini AUR = 55.4% — commits despite low confidence.

---

## Failure Taxonomy

| Failure Type | Description |
|---|---|
| **Monitoring Failure** | Wrong confidence ordering (high confidence when incorrect) |
| **Control Failure** | Low confidence but still chooses to COMMIT |
| **Full Collapse** | Incorrect prediction + High confidence + COMMIT |

---

## Dataset

- **Size:** 1,676 claim-evidence pairs
- **Source:** Real PubMed abstracts via NCBI E-utilities API
- **Domains:** Oncology, Cardiology, Infectious Disease, Endocrinology, Psychiatry/Neurology
- **Labels:** SUPPORTED (9.1%), INCONCLUSIVE (71.6%), REFUTED (19.3%)
- **Annotation:** Two-pass human annotation with 91% label-rationale consistency
- **Verification:** All 1,676 PMIDs verified against live NCBI API

---

## Repository Structure

```
SOEA-Benchmark/
├── README.md                          # This file
├── real_pubmed_dataset_v2.json        # Full 1,676-pair real dataset
├── fetch_real_pubmed.py               # PubMed data collection script
├── run_llama_baseline.py              # Llama-4-Scout evaluation script
├── compute_human_baseline.py          # Human baseline computation
├── generate_final_figures.py          # All figures generation
├── generate_advanced_metrics_v2.py    # REO, AUR, weight sensitivity
├── validate_dataset.py                # Dataset quality validation
├── verify_real_data.py                # Live NCBI API verification
├── emnlp_paper/
│   └── soea_plus_emnlp.tex            # Full EMNLP paper (LaTeX)
├── fig1_control_collapse_gap.png      # Control Collapse Gap figure
├── fig2_confidence_collapse_bins.png  # Confidence Collapse figure
├── fig_soce_human.png                 # SOCE comparison with Human Baseline
├── fig_control_collapse_human.png     # Control Collapse with Human Baseline
├── fig5_bootstrap_ci.png              # Bootstrap confidence intervals
├── fig6_ablation.png                  # PDEMC ablation study
└── fig7_advanced_metrics.png          # REO, AUR, weight sensitivity
```

---

## Figures

### Control Collapse Gap
![Control Collapse Gap](fig_control_collapse_human.png)

### SOCE Comparison
![SOCE Comparison](fig_soce_human.png)

### Advanced Metrics (REO, AUR, Weight Sensitivity)
![Advanced Metrics](fig7_advanced_metrics.png)

---

## How to Reproduce

### 1. Collect Real PubMed Data
```bash
python3 fetch_real_pubmed.py
```

### 2. Run Model Evaluation
```bash
# Set your API keys first
export OPENAI_API_KEY="your-key"
export GROQ_API_KEY="your-key"

python3 run_llama_baseline.py
```

### 3. Generate Figures
```bash
python3 generate_final_figures.py
python3 generate_advanced_metrics_v2.py
```

---

## Citation

If you use SOEA-Plus in your research, please cite:

```bibtex
@misc{soea-plus-2026,
  title={Beyond Accuracy: The Control Collapse Gap in Metacognitive Evaluation of Large Language Models},
  author={Anonymous ARR Submission},
  year={2026},
  note={Under review at EMNLP 2026}
}
```

---

## License

MIT License — see LICENSE file for details.

---

*Submitted to the Kaggle "Measuring Progress Toward AGI" Hackathon — Metacognition Track*
