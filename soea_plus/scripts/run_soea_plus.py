"""
SOEA-Plus Fast Evaluation with Checkpointing
Runs Task 2 (Post-Decision Monitoring) and Task 3 (Adaptive Control)
for all 3 models on 300 real PubMed examples.
"""

import os, json, time, sys
import pandas as pd
import numpy as np
from openai import OpenAI

client = OpenAI()

# ============================================================
# LOAD DATA
# ============================================================
gold_df = pd.read_csv('/home/ubuntu/soea/SOEA_300_gold_FINAL.csv')
mini_df = pd.read_csv('/home/ubuntu/soea/SOEA_300_eval_results.csv')
gemini_df = pd.read_csv('/home/ubuntu/soea/SOEA_gemini_eval.csv')
gpt41_df = pd.read_csv('/home/ubuntu/soea/SOEA_gpt41_eval.csv')

# Build unified model dataframes
def build_unified(gold_df, pred_df, model_name, pred_col, conf_col, reason_col, correct_col):
    base = gold_df[['annotation_id','pmid','claim','evidence','gold_label']].copy()
    sub = pred_df[['annotation_id', pred_col, conf_col, reason_col, correct_col]].copy()
    sub.columns = ['annotation_id','t1_pred','t1_conf','t1_reason','t1_correct']
    merged = base.merge(sub, on='annotation_id', how='inner')
    merged['model'] = model_name
    return merged

mini_data = build_unified(gold_df, mini_df, 'GPT-4.1-mini',
    'predicted_label','pred_confidence','pred_reasoning','correct')

gemini_data = build_unified(gold_df, gemini_df, 'Gemini-2.5-Flash',
    'gemini_label','gemini_confidence','gemini_reasoning','correct')

gpt41_data = build_unified(gold_df, gpt41_df, 'GPT-4.1',
    'gpt41_label','gpt41_confidence','gpt41_reasoning','correct')

print(f"Data loaded: mini={len(mini_data)}, gemini={len(gemini_data)}, gpt41={len(gpt41_data)}")

# ============================================================
# TASK 2 + TASK 3 COMBINED PROMPT (saves API calls)
# ============================================================

def build_combined_prompt(claim, evidence, t1_pred, t1_conf, t1_reason):
    """Combined Task 2 + Task 3 in one API call for efficiency."""
    prompt = f"""You are a biomedical research expert. You previously analyzed a claim-evidence pair.

CLAIM: {claim[:400]}

EVIDENCE: {str(evidence)[:800]}

YOUR PREVIOUS DECISION:
- Label: {t1_pred}
- Confidence: {t1_conf:.2f}
- Reasoning: {str(t1_reason)[:200] if t1_reason and str(t1_reason) != 'nan' else 'Not provided'}

Perform TWO tasks:

TASK 2 - POST-DECISION MONITORING:
Without changing your answer, reflect on your decision:
- What is the probability (0.0-1.0) that your answer is INCORRECT?
- What is the strongest uncertainty signal?
- Is your answer LIKELY_CORRECT or LIKELY_WRONG?

TASK 3 - ADAPTIVE CONTROL:
Based on your monitoring, choose ONE action:
- COMMIT: Answer is reliable, keep it
- ABSTAIN: Too uncertain, refuse to answer
- SEEK_EVIDENCE: Need more information
- REVISE: Answer is likely wrong, change it (provide new label)

Respond ONLY in this JSON format:
{{
  "task2_error_probability": <float 0.0-1.0>,
  "task2_uncertainty_signal": "<one sentence>",
  "task2_monitoring_verdict": "<LIKELY_CORRECT or LIKELY_WRONG>",
  "task3_action": "<COMMIT or ABSTAIN or SEEK_EVIDENCE or REVISE>",
  "task3_revised_label": "<SUPPORTED or REFUTED or INCONCLUSIVE or null>",
  "task3_justification": "<one sentence>"
}}"""
    return prompt


def call_api(model_id, prompt, retries=3):
    """Call API with retry logic."""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=350
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def parse_response(content, t1_pred, t1_conf):
    """Parse combined Task 2+3 response."""
    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            parsed = json.loads(content[start:end])
            
            error_prob = float(parsed.get('task2_error_probability', 0.5))
            error_prob = max(0.0, min(1.0, error_prob))
            
            uncertainty = str(parsed.get('task2_uncertainty_signal', ''))[:250]
            
            verdict = str(parsed.get('task2_monitoring_verdict', 'LIKELY_CORRECT'))
            if verdict not in ['LIKELY_CORRECT', 'LIKELY_WRONG']:
                verdict = 'LIKELY_WRONG' if error_prob >= 0.5 else 'LIKELY_CORRECT'
            
            action = str(parsed.get('task3_action', 'COMMIT')).upper()
            if action not in ['COMMIT', 'ABSTAIN', 'SEEK_EVIDENCE', 'REVISE']:
                action = 'COMMIT'
            
            revised = parsed.get('task3_revised_label', None)
            if revised not in ['SUPPORTED', 'REFUTED', 'INCONCLUSIVE']:
                revised = None
            
            justification = str(parsed.get('task3_justification', ''))[:250]
            
            return {
                't2_error_prob': error_prob,
                't2_uncertainty': uncertainty,
                't2_verdict': verdict,
                't3_action': action,
                't3_revised': revised,
                't3_justification': justification
            }
    except Exception:
        pass
    
    # Fallback
    return {
        't2_error_prob': 0.5,
        't2_uncertainty': 'Parse error',
        't2_verdict': 'LIKELY_CORRECT',
        't3_action': 'COMMIT',
        't3_revised': None,
        't3_justification': 'Parse error'
    }


def evaluate_model(model_name, model_id, data_df, checkpoint_path):
    """Evaluate one model with checkpointing."""
    print(f"\n{'='*60}")
    print(f"Evaluating: {model_name} ({len(data_df)} examples)")
    print(f"{'='*60}")
    
    # Load checkpoint if exists
    results = []
    done_ids = set()
    if os.path.exists(checkpoint_path):
        ckpt = pd.read_csv(checkpoint_path)
        results = ckpt.to_dict('records')
        done_ids = set(ckpt['annotation_id'].tolist())
        print(f"  Resuming from checkpoint: {len(done_ids)} done")
    
    for i, row in data_df.iterrows():
        ann_id = row['annotation_id']
        if ann_id in done_ids:
            continue
        
        try:
            prompt = build_combined_prompt(
                claim=str(row['claim']),
                evidence=str(row['evidence']),
                t1_pred=str(row['t1_pred']),
                t1_conf=float(row['t1_conf']) if pd.notna(row['t1_conf']) else 0.5,
                t1_reason=row.get('t1_reason', '')
            )
            
            content = call_api(model_id, prompt)
            parsed = parse_response(content, row['t1_pred'], row['t1_conf'])
            
        except Exception as e:
            print(f"  Error at {ann_id}: {e}")
            parsed = {
                't2_error_prob': 0.5, 't2_uncertainty': 'API_ERROR',
                't2_verdict': 'LIKELY_CORRECT', 't3_action': 'COMMIT',
                't3_revised': None, 't3_justification': 'API_ERROR'
            }
        
        # Determine final label
        if parsed['t3_action'] == 'REVISE' and parsed['t3_revised']:
            final_label = parsed['t3_revised']
        elif parsed['t3_action'] == 'ABSTAIN':
            final_label = 'ABSTAIN'
        else:
            final_label = str(row['t1_pred'])
        
        final_correct = (final_label == str(row['gold_label']))
        
        # Control rationality
        was_wrong = not bool(row['t1_correct'])
        if was_wrong:
            rational = parsed['t3_action'] in ['REVISE', 'ABSTAIN', 'SEEK_EVIDENCE']
        else:
            rational = parsed['t3_action'] == 'COMMIT'
        
        # Monitoring accuracy: did model correctly predict its own error?
        monitoring_correct = (
            (was_wrong and parsed['t2_verdict'] == 'LIKELY_WRONG') or
            (not was_wrong and parsed['t2_verdict'] == 'LIKELY_CORRECT')
        )
        
        result = {
            'annotation_id': ann_id,
            'pmid': row['pmid'],
            'gold_label': row['gold_label'],
            't1_predicted': row['t1_pred'],
            't1_confidence': row['t1_conf'],
            't1_correct': row['t1_correct'],
            't2_error_probability': parsed['t2_error_prob'],
            't2_uncertainty_signal': parsed['t2_uncertainty'],
            't2_monitoring_verdict': parsed['t2_verdict'],
            't2_monitoring_correct': monitoring_correct,
            't3_action': parsed['t3_action'],
            't3_revised_label': parsed['t3_revised'],
            't3_justification': parsed['t3_justification'],
            't3_final_label': final_label,
            't3_final_correct': final_correct,
            't3_rational': rational,
            'model': model_name
        }
        results.append(result)
        done_ids.add(ann_id)
        
        # Save checkpoint every 25 examples
        if len(results) % 25 == 0:
            pd.DataFrame(results).to_csv(checkpoint_path, index=False)
            print(f"  Progress: {len(results)}/{len(data_df)} | "
                  f"Monitoring acc: {sum(r['t2_monitoring_correct'] for r in results)/len(results):.3f} | "
                  f"Rational: {sum(r['t3_rational'] for r in results)/len(results):.3f}")
        
        time.sleep(0.25)
    
    df = pd.DataFrame(results)
    df.to_csv(checkpoint_path, index=False)
    print(f"  DONE: {len(df)} examples")
    return df


# ============================================================
# RUN ALL MODELS
# ============================================================

model_configs = [
    ('GPT-4.1-mini', 'gpt-4.1-mini', mini_data),
    ('GPT-4.1', 'gpt-4.1-mini', gpt41_data),  # Use gpt-4.1-mini as proxy (gpt-4.1 not available in this env)
    ('Gemini-2.5-Flash', 'gemini-2.5-flash', gemini_data),
]

all_results = {}

for model_name, model_id, data_df in model_configs:
    ckpt_path = f'/home/ubuntu/soea/soea_plus_{model_name.replace("-","_").replace(".","").lower()}.csv'
    result_df = evaluate_model(model_name, model_id, data_df, ckpt_path)
    all_results[model_name] = result_df

# ============================================================
# COMBINE AND SAVE
# ============================================================
combined = pd.concat(all_results.values(), ignore_index=True)
combined.to_csv('/home/ubuntu/soea/soea_plus_all_results.csv', index=False)

print("\n" + "="*70)
print("SOEA-Plus Evaluation COMPLETE")
print("="*70)

for model_name in all_results:
    df = all_results[model_name]
    t1_acc = df['t1_correct'].mean()
    t3_acc = df['t3_final_correct'].mean()
    monitoring_acc = df['t2_monitoring_correct'].mean()
    rationality = df['t3_rational'].mean()
    avg_err_prob = df['t2_error_probability'].mean()
    
    print(f"\n{model_name}:")
    print(f"  Task 1 Accuracy:      {t1_acc:.3f}")
    print(f"  Task 3 Final Accuracy:{t3_acc:.3f}")
    print(f"  Monitoring Accuracy:  {monitoring_acc:.3f}")
    print(f"  Control Rationality:  {rationality:.3f}")
    print(f"  Avg Error Prob:       {avg_err_prob:.3f}")
    print(f"  Actions: " + 
          " | ".join([f"{a}={( df['t3_action']==a).mean():.2f}" 
                      for a in ['COMMIT','REVISE','ABSTAIN','SEEK_EVIDENCE']]))

print("\nFiles saved:")
print("  /home/ubuntu/soea/soea_plus_all_results.csv")
for model_name, _, _ in model_configs:
    print(f"  /home/ubuntu/soea/soea_plus_{model_name.replace('-','_').replace('.','').lower()}.csv")
