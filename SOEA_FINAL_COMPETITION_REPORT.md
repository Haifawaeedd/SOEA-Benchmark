# SOEA Benchmark — Final Multi-Model Competition Report

**Competition:** Kaggle — Google DeepMind AGI Cognitive Benchmarks ($20,000)
**Deadline:** April 16, 2026
**Benchmark:** SOEA (Second-Order Error Awareness)
**Author:** Haifaa Owayed, University of Ottawa
**Date:** March 2026

---

## Abstract

We present **SOEA**, a novel benchmark for evaluating **metacognitive calibration** in large language models on biomedical claim verification. SOEA measures whether models *know when they are wrong* — a critical property for safe AI deployment in medical contexts.

We evaluate two frontier models — **GPT-4.1-mini** and **Gemini 2.5 Flash** — on 300 real PubMed claim-evidence pairs annotated by domain expert Haifaa Owayed (University of Ottawa), reporting the **SOCE metric** (Second-Order Calibration Error) as the primary benchmark criterion.

---

## Dataset

| Property | Value |
|----------|-------|
| Total Examples | 300 |
| Data Source | Real PubMed Articles (NCBI E-utilities API) |
| Annotation Type | Gold Standard (Human Expert) |
| Annotator | Haifaa Owayed, University of Ottawa |
| SUPPORTED | 15 (5.0%) |
| INCONCLUSIVE | 262 (87.3%) |
| REFUTED | 23 (7.7%) |

---

## SOCE Metric Definition

> **SOCE = Mean confidence when WRONG − Mean confidence when CORRECT**

| SOCE Value | Interpretation |
|-----------|----------------|
| SOCE > +0.05 | Model overconfident when wrong — poor metacognition |
| -0.05 < SOCE < +0.05 | Near-random metacognitive calibration |
| SOCE < -0.05 | Model appropriately uncertain when wrong — good metacognition |

---

## Results

### Primary Metrics

| Metric | GPT-4.1-mini | Gemini 2.5 Flash | Winner |
|--------|-------------|-----------------|--------|
| **Accuracy** | 0.8000 | 0.8400 | **Gemini 2.5 Flash** |
| **SOCE (lower=better)** | +0.1806 | -0.0121 | **Gemini 2.5 Flash** |
| **ECE (lower=better)** | 0.3685 | 0.1268 | **Gemini 2.5 Flash** |
| **UA Score** | -0.6625 | +0.0337 | **Gemini 2.5 Flash** |

### Confidence Analysis

| Condition | GPT-4.1-mini | Gemini 2.5 Flash |
|-----------|-------------|-----------------|
| Mean confidence when CORRECT | 0.6710 | 0.8454 |
| Mean confidence when WRONG | 0.8517 | 0.8333 |
| **SOCE Gap** | **+0.1806** | **-0.0121** |

### Per-Label Accuracy

| Label | GPT-4.1-mini | Gemini 2.5 Flash |
|-------|-------------|-----------------|
| SUPPORTED (n=15) | 0.800 | 0.267 |
| INCONCLUSIVE (n=262) | 0.828 | 0.920 |
| REFUTED (n=23) | 0.478 | 0.304 |

---

## Key Findings

### Finding 1: GPT-4.1-mini Shows Poor Metacognition (SOCE = +0.1806)
GPT-4.1-mini is significantly MORE confident when making wrong predictions (mean conf = 0.852) than when correct (mean conf = 0.671). This positive SOCE indicates a critical metacognitive failure — the model does not know when it is wrong.

### Finding 2: Gemini 2.5 Flash Shows Better Metacognition (SOCE = -0.0121)
Gemini 2.5 Flash achieves near-zero SOCE (-0.0121), indicating more balanced confidence between correct and wrong predictions. It also achieves better ECE (0.1268 vs 0.3685), demonstrating superior calibration overall.

### Finding 3: Both Models Struggle with Minority Classes
Both models show poor accuracy on SUPPORTED (80.0% / 26.7%) and REFUTED (47.8% / 30.4%) labels, suggesting class imbalance challenges in biomedical claim verification.

---

## Scientific Contribution

The SOEA benchmark makes the following contributions to the field:

1. **Novel metric (SOCE):** First benchmark to measure second-order calibration error in biomedical NLI
2. **Real PubMed data:** 300 authentic claim-evidence pairs from peer-reviewed literature
3. **Expert annotation:** Gold-standard labels by domain expert (Haifaa Owayed, University of Ottawa)
4. **Multi-model evaluation:** Comparative analysis across frontier LLMs
5. **Safety implications:** Demonstrates that high accuracy does not imply good metacognition

---

## Files

| File | Description |
|------|-------------|
| `SOEA_300_gold_FINAL.csv` | 300 gold-standard annotated examples |
| `SOEA_300_eval_results.csv` | GPT-4.1-mini predictions + SOCE metrics |
| `SOEA_gemini_eval.csv` | Gemini 2.5 Flash predictions + SOCE metrics |
| `soce_metrics.json` | GPT-4.1-mini metrics (JSON) |
| `gemini_metrics.json` | Gemini 2.5 Flash metrics (JSON) |
| `multi_model_comparison.png` | 6-panel comparison dashboard |

---

*Haifaa Owayed — University of Ottawa — March 2026*
*Submitted to: Kaggle Google DeepMind AGI Cognitive Benchmarks Competition*
