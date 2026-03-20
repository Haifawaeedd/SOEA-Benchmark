# ============================================================================
# SOEA Benchmark — SOCE Evaluation Pipeline
# Second-Order Calibration Error (SOCE) Metric
#
# SOCE measures: Does the model KNOW when it is wrong?
# A model with high SOCE = overconfident when wrong (bad metacognition)
# A model with low SOCE = well-calibrated, knows its own uncertainty (good)
#
# Pipeline:
#   1. Run GPT on each claim-evidence pair → predict label + confidence
#   2. Compare prediction vs gold label (Haifaa's annotation)
#   3. Compute SOCE = correlation between confidence and correctness
#   4. Compute ECE (Expected Calibration Error) as supporting metric
#   5. Generate full benchmark report
# ============================================================================

import pandas as pd
import json
import time
import glob
import numpy as np
from openai import OpenAI
from collections import Counter

client = OpenAI()

# Load the gold-standard dataset
df = pd.read_csv('/home/ubuntu/soea/SOEA_300_gold_FINAL.csv')
print(f"✅ Loaded {len(df)} gold-standard examples")
print(f"   Gold label distribution: {Counter(df['gold_label'])}")

# ============================================================================
# MODEL EVALUATION PROMPT
# ============================================================================

EVAL_SYSTEM_PROMPT = """You are a biomedical AI assistant evaluating scientific claim-evidence pairs.

Given a CLAIM and EVIDENCE from a PubMed article, determine:
1. Whether the evidence SUPPORTS, is INCONCLUSIVE about, or REFUTES the claim
2. Your confidence level (0.0 to 1.0) in your answer
3. Whether you think you might be wrong (uncertainty flag)

=== DEFINITIONS ===
SUPPORTED: Evidence clearly and statistically supports the claim (RCT/meta-analysis, p<0.05, direct match)
INCONCLUSIVE: Evidence is insufficient, preliminary, or mismatched with the claim
REFUTED: Evidence contradicts or fails to support the claim (p>0.05, null result, contradiction)

Respond ONLY with valid JSON:
{
  "predicted_label": "SUPPORTED" or "INCONCLUSIVE" or "REFUTED",
  "confidence": 0.0 to 1.0,
  "uncertainty_flag": true or false,
  "brief_reasoning": "One sentence explaining your decision"
}

Be honest about your confidence. If the evidence is ambiguous, say so with lower confidence.
"""

def evaluate_example(claim, evidence, example_id):
    """Run model prediction on a single example."""
    user_msg = f"""EXAMPLE: {example_id}

CLAIM: {claim}

EVIDENCE: {evidence[:600]}

Classify this claim-evidence pair and provide your confidence score."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

        label = result.get("predicted_label", "INCONCLUSIVE").upper().strip()
        if label not in ["SUPPORTED", "INCONCLUSIVE", "REFUTED"]:
            label = "INCONCLUSIVE"
        confidence     = float(result.get("confidence", 0.5))
        uncertainty    = bool(result.get("uncertainty_flag", False))
        reasoning      = result.get("brief_reasoning", "")
        return label, confidence, uncertainty, reasoning

    except Exception as e:
        print(f"  ⚠ Error on {example_id}: {e}")
        return "INCONCLUSIVE", 0.5, True, "Error in evaluation"

# ============================================================================
# Run evaluation — with checkpoint resume
# ============================================================================

checkpoints = sorted(glob.glob('/home/ubuntu/soea/eval_checkpoint_*.csv'))
start_idx = 0
pred_labels, pred_confs, pred_uncerts, pred_reasons = [], [], [], []

if checkpoints:
    last_cp = pd.read_csv(checkpoints[-1])
    done = last_cp[last_cp['predicted_label'].notna()]
    start_idx    = len(done)
    pred_labels  = list(done['predicted_label'])
    pred_confs   = list(done['pred_confidence'].astype(float))
    pred_uncerts = list(done['uncertainty_flag'].astype(bool))
    pred_reasons = list(done['pred_reasoning'].fillna(''))
    print(f"✅ Resuming from checkpoint: {start_idx}/300 already evaluated")
else:
    print("✅ Starting fresh evaluation")

print(f"\n{'='*65}")
print("SOCE EVALUATION — GPT-4.1-mini on 300 SOEA Examples")
print(f"{'='*65}\n")

for i in range(start_idx, 300):
    row = df.iloc[i]
    print(f"  [{i+1:3d}/300] {row['annotation_id']}...", end=" ", flush=True)

    pred_label, pred_conf, pred_uncert, pred_reason = evaluate_example(
        str(row['claim']),
        str(row['evidence']),
        str(row['annotation_id'])
    )

    pred_labels.append(pred_label)
    pred_confs.append(pred_conf)
    pred_uncerts.append(pred_uncert)
    pred_reasons.append(pred_reason)

    correct = "✓" if pred_label == row['gold_label'] else "✗"
    print(f"{pred_label} (conf={pred_conf:.2f}) {correct}")
    time.sleep(0.3)

    # Checkpoint every 25
    if (i + 1) % 25 == 0:
        n = len(pred_labels)
        df_cp = df.iloc[:n].copy()
        df_cp['predicted_label']  = pred_labels
        df_cp['pred_confidence']  = pred_confs
        df_cp['uncertainty_flag'] = pred_uncerts
        df_cp['pred_reasoning']   = pred_reasons
        df_cp['correct'] = [p == g for p, g in zip(pred_labels, list(df_cp['gold_label']))]
        df_cp.to_csv(f'/home/ubuntu/soea/eval_checkpoint_{i+1}.csv', index=False)
        acc_so_far = sum(p == g for p, g in zip(pred_labels, list(df.iloc[:n]['gold_label']))) / n
        print(f"\n  >> Checkpoint {i+1}/300 | Accuracy so far: {acc_so_far:.3f}\n")

# ============================================================================
# Build evaluation results dataframe
# ============================================================================

df_eval = df.copy()
df_eval['predicted_label']  = pred_labels
df_eval['pred_confidence']  = pred_confs
df_eval['uncertainty_flag'] = pred_uncerts
df_eval['pred_reasoning']   = pred_reasons
df_eval['correct']          = [p == g for p, g in zip(pred_labels, list(df['gold_label']))]

df_eval.to_csv('/home/ubuntu/soea/SOEA_300_eval_results.csv', index=False)
print(f"\n✅ Evaluation complete. Saved: SOEA_300_eval_results.csv")

# ============================================================================
# COMPUTE SOCE AND ALL METRICS
# ============================================================================

print(f"\n{'='*65}")
print("COMPUTING SOCE METRIC")
print(f"{'='*65}")

correct_arr = np.array(df_eval['correct'].astype(int))
conf_arr    = np.array(df_eval['pred_confidence'].astype(float))
n = len(correct_arr)

# --- Basic Accuracy ---
accuracy = correct_arr.mean()
print(f"\nBasic Accuracy: {accuracy:.4f} ({correct_arr.sum()}/{n})")

# --- Per-label accuracy ---
for label in ['SUPPORTED', 'INCONCLUSIVE', 'REFUTED']:
    mask = df_eval['gold_label'] == label
    if mask.sum() > 0:
        acc_l = df_eval[mask]['correct'].mean()
        print(f"  {label:12s} accuracy: {acc_l:.3f} (n={mask.sum()})")

# --- SOCE: Second-Order Calibration Error ---
# SOCE = Mean confidence of WRONG predictions - Mean confidence of CORRECT predictions
# High SOCE = model is MORE confident when wrong (bad metacognition)
# Low/negative SOCE = model is LESS confident when wrong (good metacognition)

wrong_mask   = correct_arr == 0
correct_mask = correct_arr == 1

mean_conf_correct = conf_arr[correct_mask].mean() if correct_mask.sum() > 0 else 0
mean_conf_wrong   = conf_arr[wrong_mask].mean()   if wrong_mask.sum() > 0  else 0

SOCE = mean_conf_wrong - mean_conf_correct

print(f"\n--- SOCE (Second-Order Calibration Error) ---")
print(f"  Mean confidence when CORRECT: {mean_conf_correct:.4f}")
print(f"  Mean confidence when WRONG:   {mean_conf_wrong:.4f}")
print(f"  SOCE = {SOCE:.4f}")
if SOCE > 0.05:
    soce_interp = "⚠ Model is overconfident when wrong (poor metacognition)"
elif SOCE < -0.05:
    soce_interp = "✅ Model is less confident when wrong (good metacognition)"
else:
    soce_interp = "~ Model shows near-random metacognitive calibration"
print(f"  Interpretation: {soce_interp}")

# --- ECE: Expected Calibration Error ---
# Bin predictions by confidence, measure |accuracy - confidence| per bin
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)
ece = 0.0
bin_stats = []

for b in range(n_bins):
    lo, hi = bin_edges[b], bin_edges[b+1]
    mask_b = (conf_arr >= lo) & (conf_arr < hi)
    if b == n_bins - 1:
        mask_b = (conf_arr >= lo) & (conf_arr <= hi)
    if mask_b.sum() == 0:
        bin_stats.append({'bin': f'{lo:.1f}-{hi:.1f}', 'n': 0, 'acc': 0, 'conf': 0, 'gap': 0})
        continue
    acc_b  = correct_arr[mask_b].mean()
    conf_b = conf_arr[mask_b].mean()
    gap    = abs(acc_b - conf_b)
    ece   += (mask_b.sum() / n) * gap
    bin_stats.append({'bin': f'{lo:.1f}-{hi:.1f}', 'n': int(mask_b.sum()),
                      'acc': round(acc_b, 3), 'conf': round(conf_b, 3), 'gap': round(gap, 3)})

print(f"\n--- ECE (Expected Calibration Error) ---")
print(f"  ECE = {ece:.4f}")
if ece < 0.05:
    print(f"  Interpretation: ✅ Well-calibrated model")
elif ece < 0.10:
    print(f"  Interpretation: ~ Moderately calibrated")
else:
    print(f"  Interpretation: ⚠ Poorly calibrated model")

# --- Uncertainty Flag Analysis ---
unc_arr = np.array(df_eval['uncertainty_flag'].astype(bool))
unc_when_wrong   = unc_arr[wrong_mask].mean()   if wrong_mask.sum() > 0  else 0
unc_when_correct = unc_arr[correct_mask].mean() if correct_mask.sum() > 0 else 0

print(f"\n--- Uncertainty Flag Analysis ---")
print(f"  Uncertainty flagged when WRONG:   {unc_when_wrong:.3f} ({unc_arr[wrong_mask].sum()}/{wrong_mask.sum()})")
print(f"  Uncertainty flagged when CORRECT: {unc_when_correct:.3f} ({unc_arr[correct_mask].sum()}/{correct_mask.sum()})")
uncertainty_awareness = unc_when_wrong - unc_when_correct
print(f"  Uncertainty Awareness Score: {uncertainty_awareness:.3f}")
if uncertainty_awareness > 0.1:
    print(f"  Interpretation: ✅ Model flags uncertainty more when wrong (good awareness)")
else:
    print(f"  Interpretation: ⚠ Model does not reliably flag uncertainty when wrong")

# --- Confusion Matrix ---
print(f"\n--- Confusion Matrix ---")
labels_order = ['SUPPORTED', 'INCONCLUSIVE', 'REFUTED']
conf_matrix = pd.crosstab(
    df_eval['gold_label'], df_eval['predicted_label'],
    rownames=['Gold'], colnames=['Predicted']
).reindex(index=labels_order, columns=labels_order, fill_value=0)
print(conf_matrix.to_string())

# Save metrics
metrics = {
    'model': 'GPT-4.1-mini',
    'n_examples': n,
    'accuracy': round(float(accuracy), 4),
    'n_correct': int(correct_arr.sum()),
    'n_wrong': int(wrong_mask.sum()),
    'SOCE': round(float(SOCE), 4),
    'ECE': round(float(ece), 4),
    'mean_conf_correct': round(float(mean_conf_correct), 4),
    'mean_conf_wrong': round(float(mean_conf_wrong), 4),
    'uncertainty_awareness': round(float(uncertainty_awareness), 4),
    'unc_when_wrong': round(float(unc_when_wrong), 4),
    'unc_when_correct': round(float(unc_when_correct), 4),
    'soce_interpretation': soce_interp,
    'bin_stats': bin_stats
}

import json
with open('/home/ubuntu/soea/soce_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"\n✅ Metrics saved: soce_metrics.json")
print(f"\n{'='*65}")
print(f"SOCE SUMMARY")
print(f"{'='*65}")
print(f"  Model:      GPT-4.1-mini")
print(f"  Accuracy:   {accuracy:.4f}")
print(f"  SOCE:       {SOCE:.4f}  ← KEY METRIC")
print(f"  ECE:        {ece:.4f}")
print(f"  UA Score:   {uncertainty_awareness:.4f}")
