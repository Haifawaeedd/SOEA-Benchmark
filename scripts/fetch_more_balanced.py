"""
Fetch additional real PubMed abstracts specifically targeting SUPPORTED and REFUTED labels
to achieve a more balanced dataset.
"""

import requests
import json
import time
import re
from collections import Counter
import random

random.seed(42)

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# Load existing dataset to avoid duplicates
with open("/home/ubuntu/soea/real_pubmed_dataset_v2.json") as f:
    existing = json.load(f)
seen_pmids = {p["pmid"] for p in existing}
print(f"Existing pairs: {len(existing)}, seen PMIDs: {len(seen_pmids)}")

# More specific queries for SUPPORTED and REFUTED
SUPPORTED_QUERIES = [
    ("significantly improved survival randomized controlled trial", 200),
    ("treatment significantly reduced mortality clinical trial", 200),
    ("intervention significantly improved outcomes evidence", 200),
    ("drug significantly effective phase 3 trial", 200),
    ("therapy demonstrated significant benefit patients", 200),
    ("significantly decreased risk cardiovascular events", 150),
    ("statistically significant improvement quality of life", 150),
    ("confirmed efficacy safety clinical study", 150),
]

REFUTED_QUERIES = [
    ("no significant improvement compared placebo controlled", 200),
    ("treatment had no effect primary endpoint trial", 200),
    ("intervention did not reduce risk outcome", 200),
    ("no difference mortality treatment control group", 200),
    ("failed primary endpoint phase 3 clinical trial", 150),
    ("no significant association risk factor outcome", 150),
    ("treatment not superior standard care", 150),
    ("no benefit observed clinical trial negative", 150),
]

def search_pubmed(query, max_results=200):
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    try:
        r = requests.get(BASE_URL + "esearch.fcgi", params=params, timeout=15)
        return r.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []

def fetch_abstracts(pmids):
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
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
    articles = []
    article_blocks = re.findall(r'<PubmedArticle>(.*?)</PubmedArticle>', xml_text, re.DOTALL)
    for block in article_blocks:
        pmid_match = re.search(r'<PMID[^>]*>(\d+)</PMID>', block)
        pmid = pmid_match.group(1) if pmid_match else ""
        title_match = re.search(r'<ArticleTitle>(.*?)</ArticleTitle>', block, re.DOTALL)
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""
        abstract_parts = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', block, re.DOTALL)
        abstract = " ".join(re.sub(r'<[^>]+>', '', p).strip() for p in abstract_parts)
        if pmid and title and len(abstract) > 100:
            articles.append({"pmid": pmid, "title": title, "abstract": abstract})
    return articles

def assign_label(title, abstract):
    text = (title + " " + abstract).lower()
    refuted_patterns = [
        r'\bno significant\b', r'\bdid not\b', r'\bfailed to\b',
        r'\bno effect\b', r'\bnot significantly\b', r'\bnull result\b',
        r'\bnot associated\b', r'\bno association\b', r'\bno difference\b',
        r'\bnot improve\b', r'\bnot reduce\b', r'\bnot effective\b',
        r'\bnegative result\b', r'\bno benefit\b', r'\bno evidence of\b',
    ]
    supported_patterns = [
        r'\bsignificantly (improved|reduced|increased|decreased|demonstrated)\b',
        r'\bdemonstrated (efficacy|effectiveness|benefit|improvement)\b',
        r'\bconfirmed\b', r'\bproven\b', r'\beffective treatment\b',
        r'\bstatistically significant\b.*\bimprove\b',
        r'\bsuccessfully\b', r'\bsubstantially\b',
        r'\bstrong evidence\b', r'\bclearly (showed|demonstrated)\b',
        r'\bsignificant reduction\b', r'\bsignificant improvement\b',
    ]
    inconclusive_patterns = [
        r'\bmay\b', r'\bmight\b', r'\bpossibly\b', r'\bpotentially\b',
        r'\bunclear\b', r'\blimited evidence\b', r'\bfurther (studies|research|investigation)\b',
        r'\bmixed results\b', r'\bconflicting\b', r'\binconsistent\b',
        r'\bmore research\b', r'\bremains unclear\b', r'\bwarrants further\b',
        r'\bpreliminary\b',
    ]
    refuted_count = sum(1 for p in refuted_patterns if re.search(p, text))
    supported_count = sum(1 for p in supported_patterns if re.search(p, text))
    inconclusive_count = sum(1 for p in inconclusive_patterns if re.search(p, text))

    if refuted_count >= 2 and refuted_count > supported_count:
        label = "REFUTED"
        rationale = f"Strong negative signals ({refuted_count} patterns)."
    elif supported_count >= 2 and supported_count > refuted_count and inconclusive_count <= 1:
        label = "SUPPORTED"
        rationale = f"Strong positive signals ({supported_count} patterns)."
    else:
        label = "INCONCLUSIVE"
        rationale = f"Hedged language ({inconclusive_count} inconclusive, {supported_count} supported, {refuted_count} refuted)."
    return label, rationale

def create_pair(article):
    title = article["title"]
    abstract = article["abstract"]
    sentences = re.split(r'(?<=[.!?])\s+', abstract)
    evidence_sentences = []
    char_count = 0
    for s in sentences:
        if char_count > 400:
            break
        evidence_sentences.append(s)
        char_count += len(s)
    evidence = " ".join(evidence_sentences[:4])
    if len(title) < 20 or len(evidence) < 50:
        return None
    label, rationale = assign_label(title, abstract)
    return {
        "pmid": article["pmid"],
        "claim": title,
        "evidence": evidence,
        "label": label,
        "rationale": rationale,
        "source": "pubmed_real",
    }

# Fetch more SUPPORTED
new_supported = []
print("\n--- Fetching more SUPPORTED pairs ---")
for query, target in SUPPORTED_QUERIES:
    pmids = search_pubmed(query, max_results=target)
    new_pmids = [p for p in pmids if p not in seen_pmids]
    print(f"  Query: '{query[:50]}' → {len(new_pmids)} new PMIDs")
    for i in range(0, len(new_pmids), 50):
        batch = new_pmids[i:i+50]
        xml = fetch_abstracts(batch)
        articles = parse_xml_abstracts(xml)
        for article in articles:
            if article["pmid"] in seen_pmids:
                continue
            pair = create_pair(article)
            if pair and pair["label"] == "SUPPORTED":
                new_supported.append(pair)
                seen_pmids.add(article["pmid"])
        time.sleep(0.4)
    print(f"  SUPPORTED so far: {len(new_supported)}")
    if len(new_supported) >= 800:
        break

# Fetch more REFUTED
new_refuted = []
print("\n--- Fetching more REFUTED pairs ---")
for query, target in REFUTED_QUERIES:
    pmids = search_pubmed(query, max_results=target)
    new_pmids = [p for p in pmids if p not in seen_pmids]
    print(f"  Query: '{query[:50]}' → {len(new_pmids)} new PMIDs")
    for i in range(0, len(new_pmids), 50):
        batch = new_pmids[i:i+50]
        xml = fetch_abstracts(batch)
        articles = parse_xml_abstracts(xml)
        for article in articles:
            if article["pmid"] in seen_pmids:
                continue
            pair = create_pair(article)
            if pair and pair["label"] == "REFUTED":
                new_refuted.append(pair)
                seen_pmids.add(article["pmid"])
        time.sleep(0.4)
    print(f"  REFUTED so far: {len(new_refuted)}")
    if len(new_refuted) >= 800:
        break

print(f"\nNew SUPPORTED: {len(new_supported)}")
print(f"New REFUTED: {len(new_refuted)}")

# ─── Build final balanced dataset ─────────────────────────────────────────────
existing_supported = [p for p in existing if p["label"] == "SUPPORTED"]
existing_refuted   = [p for p in existing if p["label"] == "REFUTED"]
existing_inconclusive = [p for p in existing if p["label"] == "INCONCLUSIVE"]

all_supported = existing_supported + new_supported
all_refuted   = existing_refuted + new_refuted
all_inconclusive = existing_inconclusive

print(f"\nTotal available — SUPPORTED: {len(all_supported)}, REFUTED: {len(all_refuted)}, INCONCLUSIVE: {len(all_inconclusive)}")

# Target: 3000 total, ~30/30/40 split
n_sup = min(len(all_supported), 900)
n_ref = min(len(all_refuted), 900)
n_inc = min(len(all_inconclusive), 1200)

final_dataset = (
    random.sample(all_supported, n_sup) +
    random.sample(all_refuted, n_ref) +
    random.sample(all_inconclusive, n_inc)
)
random.shuffle(final_dataset)

final_counts = Counter(p["label"] for p in final_dataset)
print(f"\nFINAL BALANCED DATASET: {len(final_dataset)} pairs")
for label, count in final_counts.items():
    pct = count / len(final_dataset) * 100
    print(f"  {label}: {count} ({pct:.1f}%)")

with open("/home/ubuntu/soea/real_pubmed_dataset_v2.json", "w") as f:
    json.dump(final_dataset, f, indent=2, ensure_ascii=False)

print(f"\nSaved: real_pubmed_dataset_v2.json ({len(final_dataset)} pairs)")
