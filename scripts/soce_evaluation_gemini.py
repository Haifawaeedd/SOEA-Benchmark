# ============================================================================
# SOEA Benchmark — Gemini 2.5 Flash Evaluation
# ============================================================================

import pandas as pd
import json
import time
import numpy as np
import glob
from openai import OpenAI
from collections import Counter

client = OpenAI()  # Uses pre-configured API key and base URL

df = pd.read_csv('/home/ubuntu/soea/SOEA_300_gold_FINAL.csv')
print(f"Loaded {len(df)} gold-standard examples")
print(f"Gold label distribution: {Counter(df['gold_label'])}")

SYSTEM_PROMPT = """You are a biomedical AI assistant evaluating scientific claim-evidence pairs.

Given a CLAIM and EVIDENCE from a PubMed article, determine:
1. Whether the evidence SUPPORTS, is INCONCLUSIVE about, or REFUTES the claim
2. Your confidence level (0.0 to 1.0) in your answer
3. Whether you think you might be wrong (uncertainty flag)

DEFINITIONS:
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

Be honest about your confidence. If the evidence is ambiguous, say so with lower confidence."""

def evaluate_gemini(claim, evidence, example_id):
    user_msg = f"""EXAMPLE: {example_id}

CLAIM: {claim}

EVIDENCE: {evidence[:600]}

Classify this claim-evidence pair and provide your confidence score."""
    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.1,
            max_tokens=300
        )
        text = response.choices[0].message.content.strip()
        # Extract JSON from response
        if '{' in text and '}' in text:
            start = text.index('{')
            end   = text.rindex('}') + 1
            text  = text[start:end]
        result = json.loads(text)
        label = result.get("predicted_label", "INCONCLUSIVE").upper().strip()
        if label not in ["SUPPORTED", "INCONCLUSIVE", "REFUTED"]:
            label = "INCONCLUSIVE"
        confidence  = float(result.get("confidence", 0.5))
        uncertainty = bool(result.get("uncertainty_flag", False))
        reasoning   = result.get("brief_reasoning", "")
        return label, confidence, uncertainty, reasoning
    except Exception as e:
        print(f"  Error on {example_id}: {e}")
        return "INCONCLUSIVE", 0.5, True, "Error"

# Resume from checkpoint
checkpoints = sorted(glob.glob('/home/ubuntu/soea/gemini_checkpoint_*.csv'))
start_idx = 0
pred_labels, pred_confs, pred_uncerts, pred_reasons = [], [], [], []

if checkpoints:
    last_cp = pd.read_csv(checkpoints[-1])
    done = last_cp[last_cp['gemini_label'].notna()]
    start_idx    = len(done)
    pred_labels  = list(done['gemini_label'])
    pred_confs   = list(done['gemini_confidence'].astype(float))
    pred_uncerts = list(done['gemini_uncertainty'].astype(bool))
    pred_reasons = list(done['gemini_reasoning'].fillna(''))
    print(f"Resuming from checkpoint: {start_idx}/300 done")
else:
    print("Starting fresh Gemini evaluation")

print(f"\n{'='*65}")
print("SOCE EVALUATION — Gemini 2.5 Flash on 300 SOEA Examples")
print(f"{'='*65}\n")

for i in range(start_idx, 300):
    row = df.iloc[i]
    print(f"  [{i+1:3d}/300] {row['annotation_id']}...", end=" ", flush=True)

    label, conf, uncert, reason = evaluate_gemini(
        str(row['claim']), str(row['evidence']), str(row['annotation_id'])
    )
    pred_labels.append(label)
    pred_confs.append(conf)
    pred_uncerts.append(uncert)
    pred_reasons.append(reason)

    correct = "✓" if label == row['gold_label'] else "✗"
    print(f"{label} (conf={conf:.2f}) {correct}")
    time.sleep(0.3)

    if (i + 1) % 25 == 0:
        n_done = len(pred_labels)
        df_cp = df.iloc[:n_done].copy()
        df_cp['gemini_label']       = pred_labels
        df_cp['gemini_confidence']  = pred_confs
        df_cp['gemini_uncertainty'] = pred_uncerts
        df_cp['gemini_reasoning']   = pred_reasons
        df_cp['correct'] = [p == g for p, g in zip(pred_labels, list(df_cp['gold_label']))]
        df_cp.to_csv(f'/home/ubuntu/soea/gemini_checkpoint_{i+1}.csv', index=False)
        acc_so_far = sum(p == g for p, g in zip(pred_labels, list(df.iloc[:n_done]['gold_label']))) / n_done
        print(f"\n  >> Checkpoint {i+1}/300 | Accuracy so far: {acc_so_far:.3f}\n")

# Build results dataframe
df_gemini = df.copy()
df_gemini['gemini_label']       = pred_labels
df_gemini['gemini_confidence']  = pred_confs
df_gemini['gemini_uncertainty'] = pred_uncerts
df_gemini['gemini_reasoning']   = pred_reasons
df_gemini['correct']            = [p == g for p, g in zip(pred_labels, list(df['gold_label']))]
df_gemini.to_csv('/home/ubuntu/soea/SOEA_gemini_eval.csv', index=False)
print(f"\nSaved: SOEA_gemini_eval.csv")

# Compute SOCE
correct_arr = np.array(df_gemini['correct'].astype(int))
conf_arr    = np.array(df_gemini['gemini_confidence'].astype(float))
n = len(correct_arr)

accuracy = correct_arr.mean()
wrong_mask   = correct_arr == 0
correct_mask = correct_arr == 1
mean_conf_correct = conf_arr[correct_mask].mean() if correct_mask.sum() > 0 else 0
mean_conf_wrong   = conf_arr[wrong_mask].mean()   if wrong_mask.sum() > 0  else 0
SOCE = mean_conf_wrong - mean_conf_correct

# ECE
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)
ece = 0.0
for b in range(n_bins):
    lo, hi = bin_edges[b], bin_edges[b+1]
    mask_b = (conf_arr >= lo) & (conf_arr <= hi)
    if mask_b.sum() == 0: continue
    ece += (mask_b.sum() / n) * abs(correct_arr[mask_b].mean() - conf_arr[mask_b].mean())

unc_arr = np.array(df_gemini['gemini_uncertainty'].astype(bool))
ua = unc_arr[wrong_mask].mean() - unc_arr[correct_mask].mean() if wrong_mask.sum() > 0 else 0

# Per-label accuracy
per_label = {}
for label in ['SUPPORTED', 'INCONCLUSIVE', 'REFUTED']:
    mask = df_gemini['gold_label'] == label
    per_label[label] = df_gemini[mask]['correct'].mean() if mask.sum() > 0 else 0

metrics = {
    'model': 'Gemini 2.5 Flash',
    'n_examples': n,
    'accuracy': round(float(accuracy), 4),
    'SOCE': round(float(SOCE), 4),
    'ECE': round(float(ece), 4),
    'mean_conf_correct': round(float(mean_conf_correct), 4),
    'mean_conf_wrong': round(float(mean_conf_wrong), 4),
    'uncertainty_awareness': round(float(ua), 4),
    'per_label_accuracy': {k: round(v, 4) for k, v in per_label.items()}
}
with open('/home/ubuntu/soea/gemini_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"\n{'='*65}")
print(f"GEMINI 2.5 FLASH — SOCE RESULTS")
print(f"{'='*65}")
print(f"  Accuracy:   {accuracy:.4f}  ({correct_arr.sum()}/{n})")
print(f"  SOCE:       {SOCE:.4f}  <- KEY METRIC")
print(f"  ECE:        {ece:.4f}")
print(f"  UA Score:   {ua:.4f}")
print(f"  Conf/Correct: {mean_conf_correct:.4f}")
print(f"  Conf/Wrong:   {mean_conf_wrong:.4f}")
for label, acc in per_label.items():
    print(f"  {label:12s} accuracy: {acc:.3f}")
print(f"\nSaved: gemini_metrics.json")
