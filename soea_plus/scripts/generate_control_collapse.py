"""
Decision vs Control Gap — "Visual Proof" of the Control Collapse Hypothesis
============================================================================
This is the single most important figure in the SOEA-Plus paper.
It proves that models do not fail at knowing — they fail at acting.
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# LOAD DATA
# ============================================================
with open('/home/ubuntu/soea/soea_plus_metrics.json', 'r') as f:
    metrics = json.load(f)

MODELS = ['GPT-4.1-mini', 'GPT-4.1', 'Gemini-2.5-Flash']
COLORS = {
    'GPT-4.1-mini': '#EF5350',      # Red — collapse
    'GPT-4.1':      '#42A5F5',      # Blue — moderate
    'Gemini-2.5-Flash': '#66BB6A',  # Green — balanced
}
MARKERS = {
    'GPT-4.1-mini': 'o',
    'GPT-4.1': 's',
    'Gemini-2.5-Flash': '^'
}

# ============================================================
# FIGURE: DECISION vs CONTROL GAP (Main visual proof)
# ============================================================

fig, axes = plt.subplots(1, 2, figsize=(18, 8))
fig.patch.set_facecolor('#0a0a1a')

# ---- LEFT PANEL: Scatter plot (the core visual proof) ----
ax = axes[0]
ax.set_facecolor('#0d1117')

# Background zones
ax.fill_between([0.75, 1.0], [0.75, 0.75], [1.0, 1.0],
                alpha=0.08, color='#66BB6A', label='_nolegend_')
ax.fill_between([0.75, 1.0], [0.4, 0.4], [0.75, 0.75],
                alpha=0.08, color='#EF5350', label='_nolegend_')

# Zone labels
ax.text(0.875, 0.92, 'BALANCED ZONE\n(Aware + Acts)', ha='center', va='center',
        fontsize=9, color='#66BB6A', alpha=0.7, style='italic')
ax.text(0.875, 0.58, 'CONTROL COLLAPSE ZONE\n(Aware but Inactive)', ha='center', va='center',
        fontsize=9, color='#EF5350', alpha=0.7, style='italic')

# Diagonal reference line (perfect alignment)
diag = np.linspace(0.75, 1.0, 100)
ax.plot(diag, diag, '--', color='white', alpha=0.25, linewidth=1.2,
        label='Perfect alignment (Monitoring = Control)')

# Plot each model
for model in MODELS:
    m = metrics[model]
    x = m['task1_accuracy']
    y = m['control_rationality']
    mon = m['monitoring_accuracy']
    
    ax.scatter(x, y, color=COLORS[model], s=350,
               marker=MARKERS[model], zorder=10,
               edgecolors='white', linewidth=1.5, label=model)
    
    # Vertical arrow showing the GAP (monitoring → control)
    ax.annotate('', xy=(x, y), xytext=(x, mon),
                arrowprops=dict(
                    arrowstyle='->', color=COLORS[model],
                    lw=2.5, connectionstyle='arc3,rad=0'
                ))
    
    # Label the gap
    gap = mon - y
    mid_y = (mon + y) / 2
    ax.text(x + 0.004, mid_y,
            f'Gap\n{gap:+.1%}',
            ha='left', va='center', fontsize=8.5,
            color=COLORS[model], fontweight='bold')
    
    # Model name label
    offset_x = -0.022 if model == 'GPT-4.1' else 0.005
    offset_y = 0.018 if model != 'Gemini-2.5-Flash' else -0.025
    ax.annotate(model,
                xy=(x, y),
                xytext=(x + offset_x, y + offset_y),
                fontsize=9.5, color='white', fontweight='bold',
                arrowprops=dict(arrowstyle='-', color='white', alpha=0.3, lw=0.8))

# Monitoring accuracy as hollow markers
for model in MODELS:
    m = metrics[model]
    ax.scatter(m['task1_accuracy'], m['monitoring_accuracy'],
               color=COLORS[model], s=150, marker=MARKERS[model],
               zorder=9, edgecolors=COLORS[model], linewidth=2,
               facecolors='none', alpha=0.8)

# Legend for hollow vs filled
filled_patch = mpatches.Patch(color='white', label='● Filled = Control Rationality (Task 3)')
hollow_patch = mpatches.Patch(facecolor='none', edgecolor='white',
                               label='○ Hollow = Monitoring Accuracy (Task 2)')
ax.legend(handles=[filled_patch, hollow_patch] +
          [mpatches.Patch(color=COLORS[m], label=m) for m in MODELS],
          fontsize=8, facecolor='#1a1a2e', edgecolor='#333355',
          labelcolor='white', loc='lower right')

ax.set_xlim(0.77, 0.87)
ax.set_ylim(0.42, 0.88)
ax.set_xlabel('Task 1 Accuracy (Decision)', color='white', fontsize=11)
ax.set_ylabel('Control Rationality / Monitoring Accuracy', color='white', fontsize=11)
ax.set_title('Decision vs Control Gap\n"Visual Proof of the Control Collapse Hypothesis"',
             color='white', fontsize=12, fontweight='bold', pad=10)
ax.tick_params(colors='white', labelsize=9)
for spine in ax.spines.values():
    spine.set_color('#333355')
ax.grid(True, alpha=0.15, color='white')
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))

# ---- RIGHT PANEL: Gap bar chart ----
ax2 = axes[1]
ax2.set_facecolor('#0d1117')

gap_data = {}
for model in MODELS:
    m = metrics[model]
    gap_data[model] = {
        'monitoring': m['monitoring_accuracy'],
        'control': m['control_rationality'],
        'gap': m['monitoring_accuracy'] - m['control_rationality']
    }

x_pos = np.arange(len(MODELS))
width = 0.32

bars_mon = ax2.bar(x_pos - width/2,
                   [gap_data[m]['monitoring'] for m in MODELS],
                   width, label='Monitoring Accuracy (Task 2)',
                   color=[COLORS[m] for m in MODELS], alpha=0.9,
                   edgecolor='white', linewidth=0.5)

bars_ctrl = ax2.bar(x_pos + width/2,
                    [gap_data[m]['control'] for m in MODELS],
                    width, label='Control Rationality (Task 3)',
                    color=[COLORS[m] for m in MODELS], alpha=0.45,
                    edgecolor='white', linewidth=0.5, hatch='///')

# Value labels
for bar in bars_mon:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h + 0.005,
             f'{h:.1%}', ha='center', va='bottom', color='white', fontsize=9, fontweight='bold')

for bar in bars_ctrl:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h + 0.005,
             f'{h:.1%}', ha='center', va='bottom', color='white', fontsize=9, fontweight='bold')

# Gap annotation arrows
for i, model in enumerate(MODELS):
    gap = gap_data[model]['gap']
    mon = gap_data[model]['monitoring']
    ctrl = gap_data[model]['control']
    mid = (mon + ctrl) / 2
    ax2.annotate('', xy=(x_pos[i] + width/2, ctrl),
                 xytext=(x_pos[i] - width/2, mon),
                 arrowprops=dict(arrowstyle='<->', color='yellow',
                                 lw=2, connectionstyle='arc3,rad=0.3'))
    ax2.text(x_pos[i] + 0.28, mid,
             f'Δ={gap:+.1%}', ha='left', va='center',
             color='yellow', fontsize=9, fontweight='bold')

ax2.set_xticks(x_pos)
ax2.set_xticklabels(MODELS, color='white', fontsize=9, rotation=10)
ax2.set_ylim(0.3, 1.0)
ax2.set_ylabel('Score', color='white', fontsize=11)
ax2.set_title('Monitoring vs Control Gap by Model\n(The Larger the Gap → The Stronger the Control Collapse)',
              color='white', fontsize=11, fontweight='bold', pad=10)
ax2.tick_params(colors='white', labelsize=9)
ax2.legend(fontsize=9, facecolor='#1a1a2e', edgecolor='#333355', labelcolor='white')
for spine in ax2.spines.values():
    spine.set_color('#333355')
ax2.yaxis.grid(True, alpha=0.15, color='white')
ax2.set_axisbelow(True)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))

# Main figure title
fig.suptitle(
    'SOEA-Plus: Control Collapse Hypothesis — Visual Proof\n'
    '"Models do not fail at knowing — they fail at acting on uncertainty."',
    fontsize=14, fontweight='bold', color='white', y=1.01
)

plt.tight_layout()
plt.savefig('/home/ubuntu/soea/soea_plus_control_collapse.png',
            dpi=160, bbox_inches='tight', facecolor='#0a0a1a')
plt.close()
print("Saved: soea_plus_control_collapse.png")

# Also copy to repo
import shutil
shutil.copy('/home/ubuntu/soea/soea_plus_control_collapse.png',
            '/home/ubuntu/SOEA-Benchmark/soea_plus/figures/soea_plus_control_collapse.png')
print("Copied to SOEA-Benchmark repo.")
