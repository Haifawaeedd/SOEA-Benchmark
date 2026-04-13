"""
Validate the real PubMed dataset and generate statistics for the paper.
"""
import json
import re
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

with open("/home/ubuntu/soea/real_pubmed_dataset_v2.json") as f:
    dataset = json.load(f)

print("=" * 60)
print(f"DATASET VALIDATION: {len(dataset)} pairs")
print("=" * 60)

# Basic stats
labels = [p["label"] for p in dataset]
label_counts = Counter(labels)
print(f"\nLabel distribution:")
for label, count in label_counts.items():
    pct = count / len(dataset) * 100
    print(f"  {label}: {count} ({pct:.1f}%)")

# Claim length stats
claim_lengths = [len(p["claim"].split()) for p in dataset]
evidence_lengths = [len(p["evidence"].split()) for p in dataset]
print(f"\nClaim length (words): mean={np.mean(claim_lengths):.1f}, median={np.median(claim_lengths):.1f}")
print(f"Evidence length (words): mean={np.mean(evidence_lengths):.1f}, median={np.median(evidence_lengths):.1f}")

# Unique PMIDs
pmids = [p["pmid"] for p in dataset]
print(f"\nUnique PMIDs: {len(set(pmids))} / {len(pmids)}")

# Domain diversity (infer from keywords in claims)
domains = {
    "Oncology": r'\bcancer\b|\btumor\b|\boncol\b|\bleukemia\b|\blymphoma\b',
    "Cardiology": r'\bcardio\b|\bheart\b|\bmyocardial\b|\bcoronary\b|\bhypertension\b',
    "Infectious Disease": r'\binfect\b|\bvirus\b|\bbacterial\b|\bCOVID\b|\bvaccine\b|\bantibiotic\b',
    "Psychiatry/Neurology": r'\bdepression\b|\banxiety\b|\bschizophrenia\b|\bcognitive\b|\bneurolog\b',
    "Endocrinology": r'\bdiabetes\b|\binsulin\b|\bthyroid\b|\bmetabolic\b',
    "Other": r'.*',
}
domain_counts = Counter()
for p in dataset:
    text = p["claim"].lower()
    assigned = False
    for domain, pattern in domains.items():
        if domain == "Other":
            continue
        if re.search(pattern, text, re.IGNORECASE):
            domain_counts[domain] += 1
            assigned = True
            break
    if not assigned:
        domain_counts["Other"] += 1

print(f"\nDomain distribution:")
for domain, count in domain_counts.most_common():
    pct = count / len(dataset) * 100
    print(f"  {domain}: {count} ({pct:.1f}%)")

# ─── Figure: Label Distribution ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Pie chart
colors = ['#2ecc71', '#e74c3c', '#f39c12']
label_names = list(label_counts.keys())
label_vals = list(label_counts.values())
axes[0].pie(label_vals, labels=label_names, colors=colors, autopct='%1.1f%%',
            startangle=90, textprops={'fontsize': 12})
axes[0].set_title('Label Distribution\n(Real PubMed Dataset, N=1,676)', fontsize=13, fontweight='bold')

# Domain bar chart
domain_names = list(domain_counts.keys())
domain_vals = list(domain_counts.values())
bar_colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12', '#95a5a6']
axes[1].barh(domain_names, domain_vals, color=bar_colors[:len(domain_names)],
             edgecolor='black', linewidth=0.7)
for i, (name, val) in enumerate(zip(domain_names, domain_vals)):
    axes[1].text(val + 5, i, f'{val}', va='center', fontsize=10)
axes[1].set_xlabel('Number of Pairs', fontsize=12)
axes[1].set_title('Domain Coverage\n(Real PubMed Dataset)', fontsize=13, fontweight='bold')
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig("/home/ubuntu/soea/fig_dataset_stats.png", dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: fig_dataset_stats.png")

# ─── Print paper-ready statistics ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("PAPER-READY STATISTICS:")
print("=" * 60)
print(f"Total pairs: {len(dataset)}")
for label, count in label_counts.items():
    pct = count / len(dataset) * 100
    print(f"  {label}: {count} ({pct:.1f}%)")
print(f"Unique PMIDs: {len(set(pmids))}")
print(f"Domains covered: {len([d for d in domain_counts if d != 'Other'])}")
print(f"Avg claim length: {np.mean(claim_lengths):.1f} words")
print(f"Avg evidence length: {np.mean(evidence_lengths):.1f} words")

# Save sample entries for paper
samples = {
    "SUPPORTED": next(p for p in dataset if p["label"] == "SUPPORTED"),
    "REFUTED": next(p for p in dataset if p["label"] == "REFUTED"),
    "INCONCLUSIVE": next(p for p in dataset if p["label"] == "INCONCLUSIVE"),
}
print("\nSample entries:")
for label, sample in samples.items():
    print(f"\n[{label}]")
    print(f"  PMID: {sample['pmid']}")
    print(f"  Claim: {sample['claim'][:100]}...")
    print(f"  Evidence: {sample['evidence'][:150]}...")
    print(f"  Rationale: {sample['rationale']}")
