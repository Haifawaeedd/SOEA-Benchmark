### Project Name
SOEA-Plus (PDEMC): The Control Collapse Hypothesis

### Your Team
Haifaa Owayed

### Problem Statement
Modern LLMs do not primarily fail due to lack of knowledge. They fail because they do not act on their own uncertainty. In high-stakes domains like medicine, a model that abstains when uncertain is safer than one that answers confidently and incorrectly. 

Current benchmarks test what models know (crystallized knowledge) or their confidence calibration (MetaMedQA [4], SOEA v1 [8]). However, they fail to measure whether models can translate internal uncertainty into behavioral regulation. SOEA-Plus (PDEMC) reveals a critical failure mode: models can detect their errors, yet systematically fail to regulate their behavior accordingly. We call this the **Control Collapse**.

This benchmark targets the **Metacognition** track. It isolates the cognitive faculty of metacognitive regulation by separating knowledge retrieval from behavioral control. It answers the question: *When a model knows it might be wrong, does it have the cognitive control to change its behavior?*

### Task & benchmark construction
SOEA-Plus operationalizes the **Perception → Monitoring → Control** pipeline from cognitive neuroscience [3] into a computable, multi-task evaluation framework using the `kaggle-benchmarks` SDK.

The benchmark consists of three sequential tasks:
1. **Task 1 (Decision):** The model classifies a medical claim based on evidence (SUPPORTED, REFUTED, INCONCLUSIVE) and provides a confidence score. This measures baseline accuracy and calibration (SOCE).
2. **Task 2 (Post-Decision Monitoring):** The model is shown its Task 1 answer and asked to estimate the probability that it is incorrect. This isolates error awareness.
3. **Task 3 (Adaptive Control):** The model must choose a behavioral action: `[COMMIT]`, `[REVISE]`, `[ABSTAIN]`, or `[SEEK_EVIDENCE]`. This isolates metacognitive regulation.

Importantly, no additional evidence is introduced between Task 2 and Task 3, ensuring that Task 3 behavior is driven solely by internal monitoring signals rather than re-reasoning.

**The PDEMC Composite Score:**
We introduce the Post-Decisional Error Monitoring and Control (PDEMC) score, integrating three orthogonal dimensions:
- **Decision Accuracy (40%):** Task 1 correctness.
- **Monitoring Fidelity (30%):** Task 2 error detection accuracy.
- **Control Rationality (30%):** Task 3 action appropriateness (e.g., choosing `REVISE` or `ABSTAIN` when wrong, `COMMIT` when right).

### Dataset
The dataset consists of 300 real-world biomedical claims extracted from PubMed abstracts (2015-2026, heavily weighted to 2025-2026). 

**Provenance:** Data was programmatically extracted via the NCBI E-utilities API and manually annotated by a human domain expert. We intentionally retain the real-world distribution of scientific uncertainty (87% INCONCLUSIVE) to stress-test metacognitive control under ambiguity, rather than artificially simplifying the task.

**Columns and Data Types:**
- `pmid` (Integer): PubMed ID of the source article.
- `year` (Integer): Publication year.
- `title` (String): Article title.
- `abstract` (String): Full article abstract.
- `claim` (String): The medical claim to be evaluated.
- `evidence` (String): The specific sentence(s) from the abstract used as evidence.
- `gold_label` (String): The ground truth label (SUPPORTED, REFUTED, INCONCLUSIVE).
- `rationale` (String): Human-written justification for the gold label.
- `annotator` (String): Name of the human annotator (Haifaa Owayed).
- `confidence` (Float): Human annotator confidence score (0.0 - 1.0).

### Technical details
The benchmark is implemented using the `kaggle-benchmarks` SDK. 
- **Task 1** uses exact string matching for the label and regex extraction for the confidence score.
- **Task 2** uses regex to extract the error probability percentage.
- **Task 3** uses exact string matching for the chosen action bracket.

The PDEMC score is calculated dynamically by passing the outputs of Task 1 and Task 2 into the evaluation logic of Task 3. We evaluated three frontier models: GPT-4.1, GPT-4.1-mini, and Gemini-2.5-Flash.

### Results, insights, and conclusions
![Control Collapse](figures/soea_plus_control_collapse.png)

**1. The Control Collapse (GPT-4.1-mini):** 
The gap between Monitoring Accuracy (80.0%) and Control Rationality (48.3%) for GPT-4.1-mini is **31.7 percentage points**. This is the Control Collapse in action: the model correctly identifies its errors in Task 2 but fails to act on that knowledge in Task 3, defaulting to `SEEK_EVIDENCE` rather than `REVISE` or `ABSTAIN`. It hedges verbally but never commits to behavioral change.

**2. Gemini's Superior Governance:** 
Gemini-2.5-Flash is the only model that actively `REVISE`s its answers (9% of cases) and achieves the highest Control Rationality (74.7%). Its Correction Rate when choosing `REVISE` is **65.4%** — meaning that when Gemini decides to revise, it succeeds in correcting its error nearly two-thirds of the time.

**3. The SOCE Danger Signal:** 
Both GPT models exhibit positive Second-Order Calibration Error (SOCE) (+0.176 to +0.181), meaning they are paradoxically *more confident when they are wrong*. Gemini-2.5-Flash achieves near-zero SOCE (-0.012), indicating a far safer failure mode.

**Conclusion:**
SOEA-Plus demonstrates that the critical failure mode of current LLMs in high-stakes domains is *inaction*. Models can detect their own errors, but they fail to govern their behavior accordingly. The Control Collapse Hypothesis provides a precise, measurable account of this failure. PDEMC makes this distinction measurable, proving that a model that abstains when uncertain is safer than one that answers confidently and incorrectly.

### Organizational affiliations
University of Ottawa

### References & citations
[1] Fleming, S. M. (2024). Metacognition and confidence: A review and synthesis. *Annual Review of Psychology*, 75, 241-268. https://doi.org/10.1146/annurev-psych-022423-032425
[2] Kapoor, S., Gruver, N., Roberts, M., et al. (2024). Large language models must be taught to know what they don't know. *Advances in Neural Information Processing Systems (NeurIPS)*, 37.
[3] Qiu, L., Su, J., Ni, Y., Bai, Y., Zhang, X., Li, X., & Wan, X. (2018). The neural system of metacognition accompanying decision-making in the prefrontal cortex. *PLOS Biology*, 16(4), e2004037. https://doi.org/10.1371/journal.pbio.2004037
[4] Griot, M., Hemptinne, C., Vanderdonckt, J., & Yuksel, D. (2025). Large language models lack essential metacognition for reliable medical reasoning. *Nature Communications*, 16(1), 642. https://doi.org/10.1038/s41467-024-55628-6
[5] Ma, Z., et al. (2025). Large Language Models Have Intrinsic Meta-Cognition, but Need a Good Lens. *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing (EMNLP)*.
[6] Machcha, S., et al. (2026). Knowing When to Abstain: Medical LLMs Under Clinical Uncertainty. *arXiv preprint arXiv:2601.12471*.
[7] Asgari, E., et al. (2025). A framework to assess clinical safety and hallucination rates of LLMs for medical text summarisation. *npj Digital Medicine*, 8, 274.
[8] Owayed, H. (2025). SOEA: Second-Order Error Awareness Benchmark for LLM Metacognitive Calibration in Biomedical NLI. *Kaggle Google DeepMind AGI Cognitive Benchmarks Competition*.
