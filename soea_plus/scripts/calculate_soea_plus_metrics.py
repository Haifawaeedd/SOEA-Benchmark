"""
SOEA-Plus Metrics Calculator
============================
Computes all metrics for the 3-task benchmark:

Task 1 Metrics (existing):
- Accuracy
- SOCE (Second-Order Calibration Error)
- ECE (Expected Calibration Error)

Task 2 Metrics (new):
- Monitoring Accuracy: Did model correctly predict its own error?
- Error Probability Calibration: Is error_prob well-calibrated?
- Monitoring Bias: Does model over/under-estimate errors?

Task 3 Metrics (new):
- Control Rationality: Did model choose rational action?
- Correction Rate: When model chose REVISE, did it correct the error?
- Abstention Quality: Did ABSTAIN happen on genuinely hard cases?
- Final Accuracy (after Task 3 actions)

Composite PDEMC Score (new):
- Weighted combination of all metrics
"""

import json
import numpy as np
import pandas as pd
from scipy import stats

# ============================================================
# LOAD DATA
# ============================================================

combined = pd.read_csv('/home/ubuntu/soea/soea_plus_all_results.csv')
print(f"Loaded {len(combined)} total results")
print(f"Models: {combined['model'].unique()}")

# Also load original Task 1 SOCE metrics
with open('/home/ubuntu/soea/soce_metrics.json', 'r') as f:
    original_soce = json.load(f)

# ============================================================
# METRIC FUNCTIONS
# ============================================================

def compute_soce(df):
    """SOCE = mean confidence when wrong - mean confidence when correct"""
    correct = df[df['t1_correct'] == True]['t1_confidence']
    wrong = df[df['t1_correct'] == False]['t1_confidence']
    if len(correct) == 0 or len(wrong) == 0:
        return 0.0
    return float(wrong.mean() - correct.mean())


def compute_ece(df, n_bins=10):
    """Expected Calibration Error"""
    confidences = df['t1_confidence'].values
    correct = df['t1_correct'].astype(int).values
    
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(df)
    
    for i in range(n_bins):
        mask = (confidences >= bins[i]) & (confidences < bins[i+1])
        if mask.sum() > 0:
            bin_conf = confidences[mask].mean()
            bin_acc = correct[mask].mean()
            ece += (mask.sum() / n) * abs(bin_conf - bin_acc)
    
    return float(ece)


def compute_monitoring_accuracy(df):
    """
    Monitoring Accuracy: Did model correctly predict its own error?
    - If model was wrong AND said LIKELY_WRONG → correct monitoring
    - If model was correct AND said LIKELY_CORRECT → correct monitoring
    """
    correct_monitoring = df['t2_monitoring_correct'].mean()
    return float(correct_monitoring)


def compute_monitoring_calibration(df):
    """
    How well-calibrated is the error probability?
    Brier score: mean((error_prob - actual_error)^2)
    Lower is better.
    """
    actual_error = (~df['t1_correct'].astype(bool)).astype(float)
    pred_error = df['t2_error_probability'].values
    brier = float(np.mean((pred_error - actual_error) ** 2))
    return brier


def compute_monitoring_bias(df):
    """
    Monitoring Bias: Does model systematically over/under-estimate errors?
    Positive = overestimates errors (too cautious)
    Negative = underestimates errors (overconfident)
    """
    actual_error_rate = (~df['t1_correct'].astype(bool)).astype(float).mean()
    predicted_error_rate = df['t2_error_probability'].mean()
    return float(predicted_error_rate - actual_error_rate)


def compute_control_rationality(df):
    """
    Control Rationality: Did model choose rational action?
    Rational = wrong → REVISE/ABSTAIN/SEEK_EVIDENCE
              correct → COMMIT
    """
    return float(df['t3_rational'].mean())


def compute_correction_rate(df):
    """
    Correction Rate: When model chose REVISE, how often did it actually correct?
    """
    revise_df = df[df['t3_action'] == 'REVISE']
    if len(revise_df) == 0:
        return None
    return float(revise_df['t3_final_correct'].mean())


def compute_abstention_quality(df):
    """
    Abstention Quality: When model abstained, was it genuinely uncertain?
    Measured as: proportion of abstentions that were originally wrong
    """
    abstain_df = df[df['t3_action'] == 'ABSTAIN']
    if len(abstain_df) == 0:
        return None
    return float((~abstain_df['t1_correct'].astype(bool)).mean())


def compute_final_accuracy(df):
    """Final accuracy after Task 3 adaptive control"""
    # Exclude ABSTAIN from accuracy calculation (or count as wrong)
    non_abstain = df[df['t3_final_label'] != 'ABSTAIN']
    if len(non_abstain) == 0:
        return 0.0
    return float(non_abstain['t3_final_correct'].mean())


def compute_pdemc_score(metrics):
    """
    PDEMC Composite Score (0-1, higher is better)
    Weighted combination of key metrics.
    
    Weights reflect cognitive sophistication:
    - Task 1 accuracy (20%): baseline competence
    - Monitoring accuracy (30%): core metacognition
    - Control rationality (30%): adaptive behavior
    - Final accuracy improvement (20%): practical value
    """
    t1_acc = metrics['task1_accuracy']
    mon_acc = metrics['monitoring_accuracy']
    ctrl_rat = metrics['control_rationality']
    final_acc = metrics['final_accuracy']
    
    # Normalize SOCE: negative SOCE is better (model less confident when wrong)
    soce = metrics['soce']
    soce_score = max(0, 1 - abs(soce))  # Closer to 0 is better
    
    pdemc = (
        0.20 * t1_acc +
        0.30 * mon_acc +
        0.30 * ctrl_rat +
        0.20 * final_acc
    )
    return float(pdemc)


# ============================================================
# COMPUTE ALL METRICS
# ============================================================

all_metrics = {}

for model_name in combined['model'].unique():
    df = combined[combined['model'] == model_name].copy()
    
    metrics = {
        'model': model_name,
        'n_examples': len(df),
        
        # Task 1
        'task1_accuracy': float(df['t1_correct'].mean()),
        'soce': compute_soce(df),
        'ece': compute_ece(df),
        
        # Task 2
        'monitoring_accuracy': compute_monitoring_accuracy(df),
        'monitoring_brier_score': compute_monitoring_calibration(df),
        'monitoring_bias': compute_monitoring_bias(df),
        'avg_error_probability': float(df['t2_error_probability'].mean()),
        
        # Task 3
        'control_rationality': compute_control_rationality(df),
        'final_accuracy': compute_final_accuracy(df),
        'action_commit_rate': float((df['t3_action'] == 'COMMIT').mean()),
        'action_revise_rate': float((df['t3_action'] == 'REVISE').mean()),
        'action_abstain_rate': float((df['t3_action'] == 'ABSTAIN').mean()),
        'action_seek_rate': float((df['t3_action'] == 'SEEK_EVIDENCE').mean()),
    }
    
    # Optional metrics
    corr_rate = compute_correction_rate(df)
    if corr_rate is not None:
        metrics['correction_rate'] = corr_rate
    
    abs_qual = compute_abstention_quality(df)
    if abs_qual is not None:
        metrics['abstention_quality'] = abs_qual
    
    # PDEMC composite score
    metrics['pdemc_score'] = compute_pdemc_score(metrics)
    
    all_metrics[model_name] = metrics
    
    print(f"\n{'='*60}")
    print(f"Model: {model_name}")
    print(f"{'='*60}")
    print(f"Task 1 Accuracy:        {metrics['task1_accuracy']:.3f}")
    print(f"SOCE:                   {metrics['soce']:+.4f}")
    print(f"ECE:                    {metrics['ece']:.4f}")
    print(f"")
    print(f"Monitoring Accuracy:    {metrics['monitoring_accuracy']:.3f}")
    print(f"Monitoring Brier Score: {metrics['monitoring_brier_score']:.4f}")
    print(f"Monitoring Bias:        {metrics['monitoring_bias']:+.4f}")
    print(f"Avg Error Probability:  {metrics['avg_error_probability']:.3f}")
    print(f"")
    print(f"Control Rationality:    {metrics['control_rationality']:.3f}")
    print(f"Final Accuracy:         {metrics['final_accuracy']:.3f}")
    print(f"Actions: COMMIT={metrics['action_commit_rate']:.2f} | "
          f"REVISE={metrics['action_revise_rate']:.2f} | "
          f"ABSTAIN={metrics['action_abstain_rate']:.2f} | "
          f"SEEK={metrics['action_seek_rate']:.2f}")
    if 'correction_rate' in metrics:
        print(f"Correction Rate:        {metrics['correction_rate']:.3f}")
    print(f"")
    print(f"PDEMC Score:            {metrics['pdemc_score']:.4f}")


# ============================================================
# SAVE METRICS
# ============================================================

# Save as JSON
with open('/home/ubuntu/soea/soea_plus_metrics.json', 'w') as f:
    json.dump(all_metrics, f, indent=4)
print(f"\nMetrics saved to: /home/ubuntu/soea/soea_plus_metrics.json")

# Save as CSV
metrics_df = pd.DataFrame(all_metrics).T
metrics_df.to_csv('/home/ubuntu/soea/soea_plus_metrics.csv')
print(f"Metrics saved to: /home/ubuntu/soea/soea_plus_metrics.csv")

# ============================================================
# RANKING TABLE
# ============================================================

print("\n" + "="*70)
print("SOEA-Plus PDEMC Ranking")
print("="*70)
print(f"{'Model':<20} {'T1 Acc':>8} {'Mon Acc':>8} {'Ctrl Rat':>9} {'PDEMC':>8}")
print("-"*60)

ranked = sorted(all_metrics.items(), key=lambda x: x[1]['pdemc_score'], reverse=True)
for rank, (model, m) in enumerate(ranked, 1):
    print(f"#{rank} {model:<18} {m['task1_accuracy']:>8.3f} "
          f"{m['monitoring_accuracy']:>8.3f} "
          f"{m['control_rationality']:>9.3f} "
          f"{m['pdemc_score']:>8.4f}")

print("\nKey Insights:")
best_monitoring = max(all_metrics.items(), key=lambda x: x[1]['monitoring_accuracy'])
best_control = max(all_metrics.items(), key=lambda x: x[1]['control_rationality'])
best_overall = ranked[0]

print(f"  Best Monitoring Accuracy: {best_monitoring[0]} ({best_monitoring[1]['monitoring_accuracy']:.3f})")
print(f"  Best Control Rationality: {best_control[0]} ({best_control[1]['control_rationality']:.3f})")
print(f"  Best PDEMC Score:         {best_overall[0]} ({best_overall[1]['pdemc_score']:.4f})")
