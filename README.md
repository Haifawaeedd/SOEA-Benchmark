# SOEA Benchmark — Second-Order Error Awareness

> **Kaggle Competition:** [Google DeepMind AGI Cognitive Benchmarks](https://www.kaggle.com/competitions/agi-cognitive-benchmarks) | Prize: $20,000 | Deadline: April 16, 2026

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Dataset](https://img.shields.io/badge/Dataset-300%20PubMed%20Examples-orange)](data/)
[![Annotator](https://img.shields.io/badge/Annotator-Haifaa%20Owayed-purple)](https://uottawa.ca)

---

## Overview

**SOEA (Second-Order Error Awareness)** is a task-specific benchmark for evaluating second-order error awareness in large language models (LLMs) — measuring whether models *know when they are wrong*, a critical metacognitive capability for safe AI deployment in biomedical domains.

Unlike traditional benchmarks that measure first-order accuracy, SOEA focuses on **metacognitive calibration**: how well a model's confidence aligns with its actual correctness.

---

## The SOCE Metric

```
SOCE = Mean confidence when WRONG − Mean confidence when CORRECT
```

This metric directly captures **directional miscalibration**: whether a model becomes more confident when it is incorrect — a key indicator of metacognitive failure.

Unlike ECE, which measures aggregate calibration error, **SOCE isolates second-order error awareness** — specifically measuring overconfidence at the point of failure.

| SOCE Value | Interpretation |
|-----------|----------------|
| SOCE > +0.05 | Model is overconfident when wrong — **poor metacognition** |
| −0.05 < SOCE < +0.05 | Near-random metacognitive calibration |
| SOCE < −0.05 | Model appropriately uncertain when wrong — **good metacognition** |

---

## Results

| Model | Accuracy | SOCE | ECE | UA Score |
|-------|----------|------|-----|----------|
| GPT-4.1-mini | 0.8000 | +0.1806 ⚠️ | 0.4795 | −0.6625 |
| GPT-4.1 | 0.8300 | +0.1762 ⚠️ | 0.3409 | — |
| Gemini 2.5 Flash | **0.8400** | **−0.0121** ✅ | **0.1268** | **+0.0337** |

### 3-Model Comparison Dashboard
![3-Model Comparison](results/3model_comparison.png)

---

## 🔥 Core Insight

GPT-4.1-mini is significantly more confident when wrong (0.852) than when correct (0.671), demonstrating a **critical metacognitive failure**.

This indicates that the model systematically misjudges its own reliability — a high-risk behavior in real-world deployment.

Both GPT models (mini and 4.1) show SOCE > +0.17, confirming a **consistent pattern of metacognitive overconfidence** in the OpenAI model family.

Gemini 2.5 Flash shows near-zero SOCE (−0.0121), suggesting significantly better metacognitive calibration.

---

## Why This Matters

Metacognitive failure — especially overconfidence in incorrect predictions — is a critical risk in high-stakes domains such as healthcare.

> A model that is wrong is expected.  
> A model that is wrong **and confident** is dangerous.

This failure is particularly dangerous in biomedical contexts, where overconfident incorrect predictions can lead to unsafe or misleading clinical decisions.

SOEA directly measures this failure mode, providing a principled evaluation framework for AI safety in biomedical NLI.

---

## Dataset

- **300 real PubMed claim-evidence pairs** sourced via NCBI E-utilities API
- **Gold-standard human annotation** by domain expert **Haifaa Owayed** (University of Ottawa)
- **Two-pass quality audit** with 91% label-rationale consistency

| Label | Count | Percentage |
|-------|-------|------------|
| SUPPORTED | 15 | 5.0% |
| INCONCLUSIVE | 262 | 87.3% |
| REFUTED | 23 | 7.7% |

The high proportion of INCONCLUSIVE cases reflects real-world scientific uncertainty in biomedical literature, where many studies provide limited, indirect, or preliminary evidence.

---

## Decision Rules

| Label | Criteria |
|-------|----------|
| **SUPPORTED** | RCT/meta-analysis, p < 0.05, n ≥ 100, evidence directly supports claim |
| **INCONCLUSIVE** | Pilot/observational, small n, hedging language, mismatch, no statistics |
| **REFUTED** | p > 0.05, null result, "no significant difference", contradicts claim |

---

## Repository Structure

```
SOEA-Benchmark/
├── data/
│   └── SOEA_300_gold_FINAL.csv          # Gold-standard annotated dataset
├── results/
│   ├── SOEA_300_eval_results.csv        # GPT-4.1-mini predictions + SOCE
│   ├── SOEA_gpt41_eval.csv              # GPT-4.1 predictions + SOCE
│   ├── SOEA_gemini_eval.csv             # Gemini 2.5 Flash predictions + SOCE
│   ├── soce_metrics.json                # GPT-4.1-mini metrics
│   ├── gpt41_metrics.json               # GPT-4.1 metrics
│   ├── gemini_metrics.json              # Gemini 2.5 Flash metrics
│   ├── 3model_comparison.png            # 3-model comparison dashboard
│   └── multi_model_comparison.png       # GPT vs Gemini comparison
├── scripts/
│   ├── collect_pubmed.py                # PubMed data collection
│   ├── gold_annotation.py               # Gold standard annotation pipeline
│   ├── soce_evaluation_gpt.py           # GPT-4.1-mini SOCE evaluation
│   └── soce_evaluation_gemini.py        # Gemini 2.5 Flash SOCE evaluation
├── SOEA_FINAL_COMPETITION_REPORT.md     # Full competition report
└── README.md
```

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Haifawaeedd/SOEA-Benchmark.git
cd SOEA-Benchmark

# Install dependencies
pip install openai pandas numpy matplotlib

# Run evaluation on your own model
python scripts/soce_evaluation_gpt.py
```

---

## Citation

```bibtex
@misc{owayed2026soea,
  title       = {SOEA: A Benchmark for Second-Order Error Awareness in Biomedical NLI},
  author      = {Owayed, Haifaa},
  year        = {2026},
  institution = {University of Ottawa},
  note        = {Submitted to Kaggle Google DeepMind AGI Cognitive Benchmarks Competition},
  url         = {https://github.com/Haifawaeedd/SOEA-Benchmark}
}
```

---

## Author

**Haifaa Owayed**  
University of Ottawa  
Kaggle: [Google DeepMind AGI Cognitive Benchmarks Competition](https://www.kaggle.com/competitions/agi-cognitive-benchmarks)

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
