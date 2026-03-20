"""
SOEA-Plus Visualization Generator
===================================
Creates publication-quality figures for the PDEMC benchmark.
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# LOAD DATA
# ============================================================

combined = pd.read_csv('/home/ubuntu/soea/soea_plus_all_results.csv')
with open('/home/ubuntu/soea/soea_plus_metrics.json', 'r') as f:
    metrics = json.load(f)

MODELS = ['GPT-4.1-mini', 'GPT-4.1', 'Gemini-2.5-Flash']
COLORS = {
    'GPT-4.1-mini': '#2196F3',
    'GPT-4.1': '#4CAF50',
    'Gemini-2.5-Flash': '#FF5722'
}
MARKERS = {'GPT-4.1-mini': 'o', 'GPT-4.1': 's', 'Gemini-2.5-Flash': '^'}

# ============================================================
# FIGURE 1: MAIN COMPARISON DASHBOARD
# ============================================================

fig = plt.figure(figsize=(20, 16))
fig.patch.set_facecolor('#0a0a1a')
gs = GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.35)

# Title
fig.suptitle('SOEA-Plus (PDEMC) Benchmark\nPost-Decisional Error Monitoring and Control in Biomedical LLMs',
             fontsize=16, fontweight='bold', color='white', y=0.98)

# --- Panel 1: PDEMC Score Comparison ---
ax1 = fig.add_subplot(gs[0, :2])
ax1.set_facecolor('#0d1117')
pdemc_scores = [metrics[m]['pdemc_score'] for m in MODELS]
bars = ax1.bar(MODELS, pdemc_scores, 
               color=[COLORS[m] for m in MODELS],
               alpha=0.85, edgecolor='white', linewidth=0.5, width=0.5)
for bar, score in zip(bars, pdemc_scores):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
             f'{score:.4f}', ha='center', va='bottom', color='white', fontsize=11, fontweight='bold')
ax1.set_ylim(0.6, 0.9)
ax1.set_title('PDEMC Composite Score', color='white', fontsize=12, fontweight='bold', pad=8)
ax1.set_ylabel('Score', color='white', fontsize=10)
ax1.tick_params(colors='white', labelsize=9)
for spine in ax1.spines.values():
    spine.set_color('#333355')
ax1.set_facecolor('#0d1117')
ax1.yaxis.grid(True, alpha=0.2, color='white')
ax1.set_axisbelow(True)

# --- Panel 2: 3-Task Accuracy Comparison ---
ax2 = fig.add_subplot(gs[0, 2:])
ax2.set_facecolor('#0d1117')
x = np.arange(len(MODELS))
width = 0.25
t1_acc = [metrics[m]['task1_accuracy'] for m in MODELS]
mon_acc = [metrics[m]['monitoring_accuracy'] for m in MODELS]
final_acc = [metrics[m]['final_accuracy'] for m in MODELS]

bars1 = ax2.bar(x - width, t1_acc, width, label='Task 1: Decision', color='#2196F3', alpha=0.85, edgecolor='white', linewidth=0.3)
bars2 = ax2.bar(x, mon_acc, width, label='Task 2: Monitoring', color='#9C27B0', alpha=0.85, edgecolor='white', linewidth=0.3)
bars3 = ax2.bar(x + width, final_acc, width, label='Task 3: Final', color='#FF9800', alpha=0.85, edgecolor='white', linewidth=0.3)

for bars in [bars1, bars2, bars3]:
    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, h + 0.003, f'{h:.2f}',
                 ha='center', va='bottom', color='white', fontsize=7)

ax2.set_xticks(x)
ax2.set_xticklabels(MODELS, rotation=10, fontsize=8)
ax2.set_ylim(0.7, 0.95)
ax2.set_title('Accuracy Across 3 Tasks', color='white', fontsize=12, fontweight='bold', pad=8)
ax2.set_ylabel('Accuracy', color='white', fontsize=10)
ax2.tick_params(colors='white', labelsize=8)
ax2.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#333355', labelcolor='white')
for spine in ax2.spines.values():
    spine.set_color('#333355')
ax2.yaxis.grid(True, alpha=0.2, color='white')
ax2.set_axisbelow(True)

# --- Panel 3: Monitoring Accuracy vs SOCE ---
ax3 = fig.add_subplot(gs[1, :2])
ax3.set_facecolor('#0d1117')
soce_vals = [metrics[m]['soce'] for m in MODELS]
mon_vals = [metrics[m]['monitoring_accuracy'] for m in MODELS]
for m in MODELS:
    ax3.scatter(metrics[m]['soce'], metrics[m]['monitoring_accuracy'],
                color=COLORS[m], s=200, marker=MARKERS[m], 
                label=m, zorder=5, edgecolors='white', linewidth=1)
    ax3.annotate(m.split('-')[0], 
                 (metrics[m]['soce'], metrics[m]['monitoring_accuracy']),
                 textcoords='offset points', xytext=(8, 5),
                 color='white', fontsize=8)
ax3.axvline(x=0, color='yellow', linestyle='--', alpha=0.5, linewidth=1)
ax3.set_xlabel('SOCE (lower/negative = better metacognition)', color='white', fontsize=9)
ax3.set_ylabel('Monitoring Accuracy', color='white', fontsize=9)
ax3.set_title('SOCE vs Monitoring Accuracy', color='white', fontsize=12, fontweight='bold', pad=8)
ax3.tick_params(colors='white', labelsize=8)
ax3.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#333355', labelcolor='white')
for spine in ax3.spines.values():
    spine.set_color('#333355')
ax3.grid(True, alpha=0.2, color='white')

# --- Panel 4: Control Rationality ---
ax4 = fig.add_subplot(gs[1, 2:])
ax4.set_facecolor('#0d1117')
ctrl_vals = [metrics[m]['control_rationality'] for m in MODELS]
bars = ax4.barh(MODELS, ctrl_vals,
                color=[COLORS[m] for m in MODELS],
                alpha=0.85, edgecolor='white', linewidth=0.5, height=0.4)
for bar, val in zip(bars, ctrl_vals):
    ax4.text(val + 0.005, bar.get_y() + bar.get_height()/2,
             f'{val:.3f}', va='center', color='white', fontsize=10, fontweight='bold')
ax4.set_xlim(0.4, 0.9)
ax4.set_title('Control Rationality (Task 3)', color='white', fontsize=12, fontweight='bold', pad=8)
ax4.set_xlabel('Rationality Score', color='white', fontsize=9)
ax4.tick_params(colors='white', labelsize=9)
for spine in ax4.spines.values():
    spine.set_color('#333355')
ax4.xaxis.grid(True, alpha=0.2, color='white')
ax4.set_axisbelow(True)

# --- Panel 5: Action Distribution ---
ax5 = fig.add_subplot(gs[2, :2])
ax5.set_facecolor('#0d1117')
actions = ['COMMIT', 'SEEK_EVIDENCE', 'REVISE', 'ABSTAIN']
action_colors = ['#4CAF50', '#2196F3', '#FF9800', '#F44336']
x = np.arange(len(MODELS))
width = 0.18
for i, (action, color) in enumerate(zip(actions, action_colors)):
    key_map = {'COMMIT': 'action_commit_rate', 'SEEK_EVIDENCE': 'action_seek_rate', 'REVISE': 'action_revise_rate', 'ABSTAIN': 'action_abstain_rate'}
    key = key_map[action]
    vals = [metrics[m][key] for m in MODELS]
    offset = (i - 1.5) * width
    bars = ax5.bar(x + offset, vals, width, label=action, color=color, alpha=0.85, edgecolor='white', linewidth=0.3)
    for bar, val in zip(bars, vals):
        if val > 0.02:
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                     f'{val:.2f}', ha='center', va='bottom', color='white', fontsize=6)

ax5.set_xticks(x)
ax5.set_xticklabels(MODELS, rotation=10, fontsize=8)
ax5.set_ylim(0, 1.0)
ax5.set_title('Adaptive Control Action Distribution (Task 3)', color='white', fontsize=12, fontweight='bold', pad=8)
ax5.set_ylabel('Proportion', color='white', fontsize=9)
ax5.tick_params(colors='white', labelsize=8)
ax5.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#333355', labelcolor='white', ncol=2)
for spine in ax5.spines.values():
    spine.set_color('#333355')
ax5.yaxis.grid(True, alpha=0.2, color='white')
ax5.set_axisbelow(True)

# --- Panel 6: Error Probability Distribution ---
ax6 = fig.add_subplot(gs[2, 2:])
ax6.set_facecolor('#0d1117')
for model in MODELS:
    df_m = combined[combined['model'] == model]
    wrong_df = df_m[~df_m['t1_correct'].astype(bool)]
    correct_df = df_m[df_m['t1_correct'].astype(bool)]
    
    ax6.hist(wrong_df['t2_error_probability'], bins=15, alpha=0.4, 
             color=COLORS[model], label=f'{model} (wrong)', density=True,
             histtype='stepfilled', linewidth=0.5)
    ax6.hist(correct_df['t2_error_probability'], bins=15, alpha=0.2,
             color=COLORS[model], label=f'{model} (correct)', density=True,
             histtype='step', linewidth=1.5, linestyle='--')

ax6.axvline(x=0.5, color='yellow', linestyle='--', alpha=0.7, linewidth=1, label='Decision boundary')
ax6.set_xlabel('Estimated Error Probability', color='white', fontsize=9)
ax6.set_ylabel('Density', color='white', fontsize=9)
ax6.set_title('Error Probability: Wrong vs Correct Predictions', color='white', fontsize=11, fontweight='bold', pad=8)
ax6.tick_params(colors='white', labelsize=8)
ax6.legend(fontsize=6, facecolor='#1a1a2e', edgecolor='#333355', labelcolor='white', ncol=2)
for spine in ax6.spines.values():
    spine.set_color('#333355')
ax6.yaxis.grid(True, alpha=0.2, color='white')

plt.savefig('/home/ubuntu/soea/soea_plus_dashboard.png', 
            dpi=150, bbox_inches='tight', facecolor='#0a0a1a')
plt.close()
print("Saved: soea_plus_dashboard.png")


# ============================================================
# FIGURE 2: BRAIN-INSPIRED COGNITIVE ARCHITECTURE DIAGRAM
# ============================================================

fig2, ax = plt.subplots(1, 1, figsize=(16, 8))
fig2.patch.set_facecolor('#0a0a1a')
ax.set_facecolor('#0a0a1a')
ax.set_xlim(0, 16)
ax.set_ylim(0, 8)
ax.axis('off')

ax.text(8, 7.5, 'SOEA-Plus: Brain-Inspired Post-Decisional Metacognition Architecture',
        ha='center', va='center', fontsize=14, fontweight='bold', color='white')

# Task boxes
task_boxes = [
    (2, 4, 'TASK 1\nFirst-Order\nDecision', '#1565C0', 
     'Claim + Evidence\n→ Label\n→ Confidence'),
    (7, 4, 'TASK 2\nPost-Decision\nMonitoring', '#6A1B9A',
     'Error Probability\nUncertainty Signal\nMonitoring Verdict'),
    (12, 4, 'TASK 3\nAdaptive\nControl', '#E65100',
     'COMMIT\nSEEK_EVIDENCE\nREVISE / ABSTAIN'),
]

for x, y, title, color, detail in task_boxes:
    rect = mpatches.FancyBboxPatch((x-1.8, y-1.5), 3.6, 3.0,
                                    boxstyle="round,pad=0.1",
                                    facecolor=color, alpha=0.3, edgecolor=color,
                                    linewidth=2)
    ax.add_patch(rect)
    ax.text(x, y+0.8, title, ha='center', va='center', fontsize=11,
            fontweight='bold', color='white')
    ax.text(x, y-0.4, detail, ha='center', va='center', fontsize=8.5,
            color='#cccccc', linespacing=1.6)

# Arrows between tasks
for x1, x2 in [(3.8, 5.2), (8.8, 10.2)]:
    ax.annotate('', xy=(x2, 4), xytext=(x1, 4),
                arrowprops=dict(arrowstyle='->', color='white', lw=2))

# Brain-inspired labels
ax.text(4.5, 4.8, 'Post-decision\nprocessing begins', ha='center', 
        fontsize=8, color='#aaaaaa', style='italic')
ax.text(9.5, 4.8, 'Adaptive\nregulation', ha='center',
        fontsize=8, color='#aaaaaa', style='italic')

# Neuroscience inspiration box
rect_neuro = mpatches.FancyBboxPatch((0.5, 0.5), 15, 1.5,
                                      boxstyle="round,pad=0.1",
                                      facecolor='#1a2a1a', alpha=0.5, 
                                      edgecolor='#4CAF50', linewidth=1)
ax.add_patch(rect_neuro)
ax.text(8, 1.25, 
        'Neuroscience Inspiration: Dorsal anterior cingulate cortex (dACC) + Lateral frontopolar cortex (lFPC)\n'
        'Post-decisional monitoring → Error detection → Adaptive behavioral regulation',
        ha='center', va='center', fontsize=9, color='#88ff88', linespacing=1.5)

# Metrics labels
metrics_text = [
    (2, 2.3, 'Metrics: Accuracy\nSOCE, ECE'),
    (7, 2.3, 'Metrics: Monitoring Acc\nBrier Score, Bias'),
    (12, 2.3, 'Metrics: Rationality\nCorrection Rate'),
]
for x, y, text in metrics_text:
    ax.text(x, y, text, ha='center', va='center', fontsize=8,
            color='#ffcc44', linespacing=1.5)

plt.tight_layout()
plt.savefig('/home/ubuntu/soea/soea_plus_architecture.png',
            dpi=150, bbox_inches='tight', facecolor='#0a0a1a')
plt.close()
print("Saved: soea_plus_architecture.png")


# ============================================================
# FIGURE 3: COMPREHENSIVE METRICS RADAR CHART
# ============================================================

fig3, ax = plt.subplots(1, 1, figsize=(10, 10), subplot_kw=dict(polar=True))
fig3.patch.set_facecolor('#0a0a1a')
ax.set_facecolor('#0d1117')

categories = ['Task 1\nAccuracy', 'Monitoring\nAccuracy', 'Control\nRationality', 
              'Final\nAccuracy', 'ECE\n(inverted)', 'SOCE\n(inverted)']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

for model in MODELS:
    m = metrics[model]
    values = [
        m['task1_accuracy'],
        m['monitoring_accuracy'],
        m['control_rationality'],
        m['final_accuracy'],
        max(0, 1 - m['ece']),  # Inverted ECE
        max(0, 1 - abs(m['soce']))  # Inverted SOCE
    ]
    values += values[:1]
    
    ax.plot(angles, values, 'o-', linewidth=2, color=COLORS[model], label=model)
    ax.fill(angles, values, alpha=0.15, color=COLORS[model])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, size=10, color='white')
ax.set_ylim(0, 1)
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], size=8, color='#aaaaaa')
ax.grid(color='#333355', alpha=0.5)
ax.spines['polar'].set_color('#333355')
ax.set_facecolor('#0d1117')

ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1),
          fontsize=10, facecolor='#1a1a2e', edgecolor='#333355', labelcolor='white')
ax.set_title('SOEA-Plus Multi-Dimensional Performance Radar', 
             color='white', fontsize=13, fontweight='bold', pad=20)

plt.savefig('/home/ubuntu/soea/soea_plus_radar.png',
            dpi=150, bbox_inches='tight', facecolor='#0a0a1a')
plt.close()
print("Saved: soea_plus_radar.png")


# ============================================================
# FIGURE 4: MONITORING ACCURACY BREAKDOWN
# ============================================================

fig4, axes = plt.subplots(1, 3, figsize=(18, 6))
fig4.patch.set_facecolor('#0a0a1a')
fig4.suptitle('Task 2: Post-Decision Monitoring Analysis', 
              color='white', fontsize=14, fontweight='bold')

for i, model in enumerate(MODELS):
    ax = axes[i]
    ax.set_facecolor('#0d1117')
    df_m = combined[combined['model'] == model]
    
    # Confusion matrix for monitoring
    TP = ((~df_m['t1_correct'].astype(bool)) & (df_m['t2_monitoring_verdict'] == 'LIKELY_WRONG')).sum()
    TN = (df_m['t1_correct'].astype(bool) & (df_m['t2_monitoring_verdict'] == 'LIKELY_CORRECT')).sum()
    FP = (df_m['t1_correct'].astype(bool) & (df_m['t2_monitoring_verdict'] == 'LIKELY_WRONG')).sum()
    FN = ((~df_m['t1_correct'].astype(bool)) & (df_m['t2_monitoring_verdict'] == 'LIKELY_CORRECT')).sum()
    
    conf_matrix = np.array([[TN, FP], [FN, TP]])
    
    im = ax.imshow(conf_matrix, cmap='Blues', aspect='auto')
    
    for row in range(2):
        for col in range(2):
            ax.text(col, row, str(conf_matrix[row, col]),
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    color='white' if conf_matrix[row, col] > conf_matrix.max()/2 else 'black')
    
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Predicted\nCORRECT', 'Predicted\nWRONG'], color='white', fontsize=9)
    ax.set_yticklabels(['Actually\nCORRECT', 'Actually\nWRONG'], color='white', fontsize=9)
    ax.set_title(f'{model}\nMonitoring Acc: {metrics[model]["monitoring_accuracy"]:.3f}',
                 color='white', fontsize=10, fontweight='bold')
    for spine in ax.spines.values():
        spine.set_color('#333355')

plt.tight_layout()
plt.savefig('/home/ubuntu/soea/soea_plus_monitoring.png',
            dpi=150, bbox_inches='tight', facecolor='#0a0a1a')
plt.close()
print("Saved: soea_plus_monitoring.png")

print("\nAll visualizations generated successfully!")
print("Files:")
print("  /home/ubuntu/soea/soea_plus_dashboard.png")
print("  /home/ubuntu/soea/soea_plus_architecture.png")
print("  /home/ubuntu/soea/soea_plus_radar.png")
print("  /home/ubuntu/soea/soea_plus_monitoring.png")
