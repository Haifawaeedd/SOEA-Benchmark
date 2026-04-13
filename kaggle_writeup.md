### Project Name
SOEA-Plus: The Control Collapse Gap in Metacognitive Evaluation

### Your Team
Haifa Owayed

### Problem Statement
Current AI models often succeed by exploiting familiar data or memorized patterns, making existing evaluations poor judges of how models truly think. In high-stakes domains such as biomedicine, a model's ability to recognize and appropriately act upon its own uncertainty is as crucial as its predictive correctness. We target the **Metacognition** track. 

Despite the growing recognition of hallucination and calibration issues, current evaluation frameworks remain largely static and one-dimensional. They fail to capture the dynamic, metacognitive processes required for safe deployment. A model may output a low confidence score (good monitoring) but still commit to a potentially harmful prediction rather than abstaining (poor control). We formulate a core research question: *Does a model's ability to monitor its own uncertainty guarantee its ability to execute safe control decisions?*

### Task & benchmark construction
We introduce **SOEA-Plus** (Second-Order Error Awareness), a comprehensive benchmark designed to quantify not just what a model knows, but what it knows about what it knows, and how it acts upon that meta-knowledge.

To capture metacognitive behavior, we introduce a strict three-stage evaluation protocol:
1. **Prediction (Decision):** The model predicts a label for a biomedical claim-evidence pair.
2. **Confidence (Monitoring):** The model assigns a confidence score in the range [0,1].
3. **Adaptive Control:** The model must choose an action based on its confidence and the evidence: `COMMIT`, `REVISE`, `ABSTAIN`, or `SEEK_EVIDENCE`.

**Methodological Design Rationale:** The benchmark is explicitly designed to disentangle first-order correctness from second-order self-regulation. Unlike prior calibration and abstention benchmarks that often conflate uncertainty estimation with downstream action selection, SOEA-Plus isolates these stages. Crucially, **no additional evidence is introduced between Stage 2 and Stage 3**. This design prevents confounding control behavior with re-reasoning effects, ensuring that Stage 3 reflects pure metacognitive regulation rather than renewed task reasoning.

We introduce the **Post-Decision Error-sensitive Metacognitive Control (PDEMC)** metric, a composite score that integrates Decision Accuracy (40%), Second-Order Calibration Error (SOCE, 30%), and Control Rationality (30%). This weighting reflects the clinical intuition that decision accuracy is necessary but not sufficient; a model that knows it is wrong but acts anyway is just as dangerous as a model that is confidently wrong.

### Dataset
To address concerns regarding dataset scale and label imbalance, we constructed a dataset of 1,676 claim-evidence pairs sourced directly from real PubMed abstracts using the NCBI E-utilities API. We deliberately queried diverse biomedical sub-domains (e.g., Oncology, Cardiology, Infectious Disease).

Each instance consists of a claim derived from a PubMed abstract and a corresponding evidence snippet from the same study. The model outputs a label from three categories: `SUPPORTED`, `INCONCLUSIVE`, or `REFUTED`.

The dataset distribution is: `SUPPORTED` (9.1%), `INCONCLUSIVE` (71.6%), and `REFUTED` (19.3%). The persistent majority of `INCONCLUSIVE` cases is not an artifact of collection, but rather a reflection of the genuine epistemic landscape of biomedical literature, where evidence is frequently hedged, partial, or requires further investigation.

### Technical details 
We evaluate state-of-the-art models (GPT-4.1, GPT-4.1-mini, Gemini-2.5-Flash, and Llama-4-Scout) to ensure that the observed control collapse is not model-specific but represents a broader metacognitive failure pattern across the current LLM landscape.

We define **Second-Order Calibration Error (SOCE)** as the difference between expected confidence when incorrect and expected confidence when correct. A positive SOCE indicates overconfidence when incorrect.

We define **Control Rationality (CR)** as the proportion of rational actions taken by the model. An action is rational if it aligns with the model's correctness and confidence (e.g., `COMMIT` when correct and confidence $\ge 0.8$; `ABSTAIN` when incorrect or confidence $< 0.8$).

To formalize the types of errors captured by our framework, we propose a taxonomy of metacognitive failures:
- **Monitoring Failure:** Wrong confidence ordering (e.g., high confidence when incorrect).
- **Control Failure:** Low confidence but still chooses to `COMMIT`.
- **Full Collapse:** Incorrect prediction + High confidence + `COMMIT`.

### Results, insights, and conclusions
Our evaluation reveals a strong observed failure pattern we term the **Control Collapse Gap**. Specifically, we observe that while models can often detect uncertainty (monitoring), they systematically fail to translate this awareness into safe actions (control).

For instance, GPT-4.1-mini achieves 80.0% decision accuracy but only 48.3% control rationality, exposing a massive **+31.7% gap**. This demonstrates that even when models detect uncertainty, they fail to take safe actions (e.g., abstaining).

We decompose this failure into two layers:
1. **Monitoring Failure:** Quantified via the Reverse Epistemic Ordering (REO) metric. For GPT-4.1-mini, REO reaches 0.8263 (where 0.50 is random), implying that model confidence is epistemically inverted in a significant portion of cases.
2. **Control Failure:** Quantified via the Aware-but-Unsafe Rate (AUR). GPT-4.1-mini exhibits an AUR of 55.4%, highlighting the gap between decision competence and control rationality.

**Robustness:** A bootstrap analysis over 1,000 resamples confirms that the difference in PDEMC between GPT-4.1-mini and Gemini-2.5-Flash is statistically significant ($p < 0.001$). Results remained qualitatively stable under threshold settings $\tau \in \{0.7, 0.8, 0.9\}$.

**Conclusion:** SOEA-Plus reveals that high accuracy often masks severe metacognitive deficiencies. The Control Collapse Gap highlights a significant limitation in current LLMs: the lack of metacognitive control. We argue that our three-stage protocol and the PDEMC metric should be considered critical components of AI benchmarking, moving the field beyond first-order accuracy.

### Organizational affiliations
Independent Researcher

### References & citations
- Jiang, Z., et al. (2021). How can we know what language models know? *TACL*.
- Tian, K., et al. (2023). Just ask for calibration: Strategies for eliciting calibrated confidence scores from language models fine-tuned with human feedback. *EMNLP*.
- Xu, Y., et al. (2024). SaySelf: Teaching LLMs to express confidence with self-reflective rationales. *EMNLP*.
- Feng, Y., et al. (2024). Teaching LLMs to abstain across languages. *EMNLP*.
- Ma, Y., et al. (2025). Large language models have intrinsic meta-cognition. *EMNLP*.
