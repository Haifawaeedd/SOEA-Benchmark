"""
Fetch REAL PubMed abstracts via NCBI E-utilities API.
No synthetic data — all claim-evidence pairs are derived from actual PubMed articles.

Strategy:
- Query multiple biomedical sub-domains to ensure diversity
- Extract claim (title or first sentence of abstract) + evidence (abstract body)
- Use rule-based heuristics to assign preliminary labels:
    SUPPORTED: abstract contains strong positive findings ("significantly", "demonstrated", "confirmed")
    REFUTED:   abstract contains negative findings ("no significant", "did not", "failed to", "no effect")
    INCONCLUSIVE: abstract contains hedged language ("may", "unclear", "limited evidence", "further studies")
- This gives a real, diverse, and balanced dataset
"""

import requests
import json
import time
import re
from collections import Counter

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# Search queries targeting different biomedical sub-domains and label types
QUERIES = [
    # SUPPORTED-leaning queries (strong positive findings)
    ("cancer immunotherapy efficacy randomized controlled trial", 200),
    ("metformin diabetes treatment significant reduction", 150),
    ("vaccine efficacy clinical trial confirmed", 150),
    ("antibiotic resistance treatment outcome significant", 150),
    ("cognitive behavioral therapy depression efficacy", 100),
    ("exercise intervention cardiovascular benefit demonstrated", 100),

    # REFUTED-leaning queries (negative findings)
    ("no significant difference treatment placebo", 200),
    ("failed to demonstrate clinical benefit", 150),
    ("no effect intervention outcome null result", 150),
    ("treatment did not improve patient outcome", 150),
    ("negative result randomized trial", 100),

    # INCONCLUSIVE-leaning queries (uncertain / mixed findings)
    ("inconclusive evidence systematic review", 200),
    ("further research needed biomedical uncertainty", 150),
    ("mixed results clinical study limitations", 150),
    ("limited evidence may suggest possible association", 150),
    ("conflicting results meta-analysis biomedical", 100),
    ("unclear mechanism potential benefit", 100),
]

def search_pubmed(query, max_results=100):
    """Search PubMed and return list of PMIDs."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "usehistory": "n",
    }
    try:
        r = requests.get(BASE_URL + "esearch.fcgi", params=params, timeout=15)
        data = r.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"Search error for '{query}': {e}")
        return []

def fetch_abstracts(pmids):
    """Fetch abstracts for a list of PMIDs."""
    if not pmids:
        return []
    ids = ",".join(pmids)
    params = {
        "db": "pubmed",
        "id": ids,
        "retmode": "xml",
        "rettype": "abstract",
    }
    try:
        r = requests.get(BASE_URL + "efetch.fcgi", params=params, timeout=20)
        return r.text
    except Exception as e:
        print(f"Fetch error: {e}")
        return ""

def parse_xml_abstracts(xml_text):
    """Parse PubMed XML to extract PMID, title, and abstract."""
    articles = []
    # Split by article
    article_blocks = re.findall(r'<PubmedArticle>(.*?)</PubmedArticle>', xml_text, re.DOTALL)
    for block in article_blocks:
        # PMID
        pmid_match = re.search(r'<PMID[^>]*>(\d+)</PMID>', block)
        pmid = pmid_match.group(1) if pmid_match else ""

        # Title
        title_match = re.search(r'<ArticleTitle>(.*?)</ArticleTitle>', block, re.DOTALL)
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""

        # Abstract — handle structured abstracts (multiple AbstractText sections)
        abstract_parts = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', block, re.DOTALL)
        abstract = " ".join(re.sub(r'<[^>]+>', '', p).strip() for p in abstract_parts)

        if pmid and title and len(abstract) > 100:
            articles.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
            })
    return articles

def assign_label(title, abstract):
    """
    Rule-based label assignment from real text signals.
    Returns (label, confidence_score, rationale)
    """
    text = (title + " " + abstract).lower()

    # REFUTED signals
    refuted_patterns = [
        r'\bno significant\b', r'\bdid not\b', r'\bfailed to\b',
        r'\bno effect\b', r'\bnot significantly\b', r'\bnull result\b',
        r'\bnot associated\b', r'\bno association\b', r'\bno difference\b',
        r'\bnot improve\b', r'\bnot reduce\b', r'\bnot effective\b',
        r'\bnegative result\b', r'\bno benefit\b', r'\bno evidence of\b',
    ]

    # SUPPORTED signals
    supported_patterns = [
        r'\bsignificantly (improved|reduced|increased|decreased|demonstrated)\b',
        r'\bdemonstrated (efficacy|effectiveness|benefit|improvement)\b',
        r'\bconfirmed\b', r'\bproven\b', r'\beffective treatment\b',
        r'\bstatistically significant\b.*\bimprove\b',
        r'\bsuccessfully\b', r'\bsubstantially\b',
        r'\bstrong evidence\b', r'\bclearly (showed|demonstrated)\b',
        r'\bsignificant reduction\b', r'\bsignificant improvement\b',
    ]

    # INCONCLUSIVE signals
    inconclusive_patterns = [
        r'\bmay\b', r'\bmight\b', r'\bpossibly\b', r'\bpotentially\b',
        r'\bunclear\b', r'\blimited evidence\b', r'\bfurther (studies|research|investigation)\b',
        r'\bmixed results\b', r'\bconflicting\b', r'\binconsistent\b',
        r'\bmore research\b', r'\bremains unclear\b', r'\bwarrants further\b',
        r'\bpreliminary\b', r'\bsuggests\b.*\bfurther\b',
    ]

    refuted_count = sum(1 for p in refuted_patterns if re.search(p, text))
    supported_count = sum(1 for p in supported_patterns if re.search(p, text))
    inconclusive_count = sum(1 for p in inconclusive_patterns if re.search(p, text))

    # Decision logic
    if refuted_count >= 2 and refuted_count > supported_count:
        label = "REFUTED"
        rationale = f"Strong negative signals ({refuted_count} patterns): no significant difference, failed to demonstrate benefit."
    elif supported_count >= 2 and supported_count > refuted_count and inconclusive_count <= 1:
        label = "SUPPORTED"
        rationale = f"Strong positive signals ({supported_count} patterns): significant improvement/reduction demonstrated."
    else:
        label = "INCONCLUSIVE"
        rationale = f"Hedged or mixed language ({inconclusive_count} inconclusive, {supported_count} supported, {refuted_count} refuted patterns)."

    return label, rationale

def create_claim_evidence_pair(article):
    """Create a claim-evidence pair from a PubMed article."""
    title = article["title"]
    abstract = article["abstract"]

    # Claim = the title (research question/hypothesis)
    claim = title

    # Evidence = first 2-3 sentences of abstract (the key findings)
    sentences = re.split(r'(?<=[.!?])\s+', abstract)
    # Take up to 3 sentences but at least 50 chars
    evidence_sentences = []
    char_count = 0
    for s in sentences:
        if char_count > 400:
            break
        evidence_sentences.append(s)
        char_count += len(s)
    evidence = " ".join(evidence_sentences[:4])

    if len(claim) < 20 or len(evidence) < 50:
        return None

    label, rationale = assign_label(title, abstract)

    return {
        "pmid": article["pmid"],
        "claim": claim,
        "evidence": evidence,
        "label": label,
        "rationale": rationale,
        "source": "pubmed_real",
    }

# ─── Main Collection Loop ──────────────────────────────────────────────────────
print("=" * 60)
print("FETCHING REAL PUBMED DATA")
print("=" * 60)

all_pairs = []
seen_pmids = set()

for query, target_count in QUERIES:
    print(f"\nQuery: '{query[:60]}...' (target: {target_count})")

    pmids = search_pubmed(query, max_results=min(target_count, 200))
    # Filter already seen
    new_pmids = [p for p in pmids if p not in seen_pmids]
    print(f"  Found {len(pmids)} PMIDs, {len(new_pmids)} new")

    if not new_pmids:
        continue

    # Fetch in batches of 50
    batch_size = 50
    for i in range(0, len(new_pmids), batch_size):
        batch = new_pmids[i:i+batch_size]
        xml = fetch_abstracts(batch)
        articles = parse_xml_abstracts(xml)

        for article in articles:
            if article["pmid"] in seen_pmids:
                continue
            pair = create_claim_evidence_pair(article)
            if pair:
                all_pairs.append(pair)
                seen_pmids.add(article["pmid"])

        print(f"  Batch {i//batch_size + 1}: fetched {len(articles)} articles, total pairs: {len(all_pairs)}")
        time.sleep(0.4)  # NCBI rate limit: max 3 req/sec without API key

    if len(all_pairs) >= 3500:
        print("Target reached, stopping early.")
        break

# ─── Label Distribution ────────────────────────────────────────────────────────
label_counts = Counter(p["label"] for p in all_pairs)
print("\n" + "=" * 60)
print(f"TOTAL PAIRS COLLECTED: {len(all_pairs)}")
print(f"Label distribution: {dict(label_counts)}")

# ─── Balance the dataset ───────────────────────────────────────────────────────
# Target: SUPPORTED ~30%, REFUTED ~30%, INCONCLUSIVE ~40%
import random
random.seed(42)

supported = [p for p in all_pairs if p["label"] == "SUPPORTED"]
refuted   = [p for p in all_pairs if p["label"] == "REFUTED"]
inconclusive = [p for p in all_pairs if p["label"] == "INCONCLUSIVE"]

print(f"\nRaw counts — SUPPORTED: {len(supported)}, REFUTED: {len(refuted)}, INCONCLUSIVE: {len(inconclusive)}")

# Determine target sizes
total_target = min(3000, len(all_pairs))
n_supported = min(len(supported), int(total_target * 0.30))
n_refuted   = min(len(refuted),   int(total_target * 0.30))
n_inconclusive = min(len(inconclusive), total_target - n_supported - n_refuted)

balanced = (
    random.sample(supported, n_supported) +
    random.sample(refuted, n_refuted) +
    random.sample(inconclusive, n_inconclusive)
)
random.shuffle(balanced)

final_counts = Counter(p["label"] for p in balanced)
print(f"\nBALANCED DATASET: {len(balanced)} pairs")
print(f"Label distribution: {dict(final_counts)}")
for label, count in final_counts.items():
    pct = count / len(balanced) * 100
    print(f"  {label}: {count} ({pct:.1f}%)")

# ─── Save ──────────────────────────────────────────────────────────────────────
with open("/home/ubuntu/soea/real_pubmed_dataset_v2.json", "w") as f:
    json.dump(balanced, f, indent=2, ensure_ascii=False)

print(f"\nSaved: real_pubmed_dataset_v2.json ({len(balanced)} pairs)")
print("Sample entry:")
print(json.dumps(balanced[0], indent=2)[:500])
