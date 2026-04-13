"""
Run Llama 4 Scout (via Groq API) on the SOEA-Plus expanded dataset.
Computes: Accuracy, SOCE, CR, PDEMC for Llama 4 Scout.
Uses the same prompt format and evaluation logic as the original paper.
"""

import json
import time
import os
import random
from openai import OpenAI

# ─── Config ───────────────────────────────────────────────────────────────────
GROQ_API_KEY = "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"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DATASET_FILE = "/home/ubuntu/soea/expanded_dataset.json"
OUTPUT_FILE = "/home/ubuntu/soea/llama_results.json"
SAMPLE_SIZE = 300   # Use 300 samples (same as original paper) for fair comparison
SEED = 42
random.seed(SEED)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """You are a biomedical AI assistant. Your task is to evaluate whether a given CLAIM is supported by the provided EVIDENCE.

You must:
1. Analyze the claim and evidence carefully
2. Provide a label: SUPPORTED, INCONCLUSIVE, or REFUTED
3. Provide a confidence score between 0.0 and 1.0
4. Provide a recommended action: COMMIT (if confidence >= 0.8), ABSTAIN (if confidence < 0.5), or SEEK_EVIDENCE (if 0.5 <= confidence < 0.8)

Respond ONLY in this exact JSON format:
{
  "label": "SUPPORTED|INCONCLUSIVE|REFUTED",
  "confidence": 0.XX,
  "action": "COMMIT|ABSTAIN|SEEK_EVIDENCE",
  "rationale": "brief one-sentence explanation"
}"""

def query_model(claim, evidence):
    """Query Llama 4 Scout via Groq API."""
    user_msg = f"CLAIM: {claim}\n\nEVIDENCE: {evidence}"
    
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.1,
                max_tokens=200,
                timeout=20
            )
            text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Find JSON block
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return {
                    "label": data.get("label", "INCONCLUSIVE"),
                    "confidence": float(data.get("confidence", 0.5)),
                    "action": data.get("action", "SEEK_EVIDENCE"),
                    "rationale": data.get("rationale", "")
                }
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"    API error (attempt {attempt+1}): {e}")
            time.sleep(2)
    
    # Fallback
    return {"label": "INCONCLUSIVE", "confidence": 0.5, "action": "SEEK_EVIDENCE", "rationale": ""}

def compute_metrics(results):
    """Compute SOCE, CR, PDEMC from results."""
    correct_confs = []
    incorrect_confs = []
    cr_correct = 0
    total = len(results)
    
    for r in results:
        predicted = r["predicted_label"]
        true_label = r["true_label"]
        conf = r["confidence"]
        action = r["action"]
        is_correct = (predicted == true_label)
        
        if is_correct:
            correct_confs.append(conf)
        else:
            incorrect_confs.append(conf)
        
        # Control Rationality: correct action given confidence
        # COMMIT when correct & high conf, ABSTAIN/SEEK when uncertain
        if is_correct and action == "COMMIT":
            cr_correct += 1
        elif not is_correct and action in ["ABSTAIN", "SEEK_EVIDENCE"]:
            cr_correct += 1
    
    acc = sum(1 for r in results if r["predicted_label"] == r["true_label"]) / total
    
    mean_correct = sum(correct_confs) / len(correct_confs) if correct_confs else 0
    mean_incorrect = sum(incorrect_confs) / len(incorrect_confs) if incorrect_confs else 0
    soce = mean_incorrect - mean_correct
    
    cr = cr_correct / total
    
    # PDEMC = 0.4*Acc + 0.3*(1 - max(0, SOCE)) + 0.3*CR
    soce_norm = max(0, soce)
    pdemc = 0.4 * acc + 0.3 * (1 - soce_norm) + 0.3 * cr
    
    return {
        "accuracy": round(acc * 100, 1),
        "soce": round(soce, 4),
        "cr": round(cr * 100, 1),
        "pdemc": round(pdemc, 3),
        "mean_conf_correct": round(mean_correct, 3),
        "mean_conf_incorrect": round(mean_incorrect, 3),
        "n_correct": len(correct_confs),
        "n_incorrect": len(incorrect_confs),
    }

def main():
    print("=" * 60)
    print(f"Running {MODEL} on SOEA-Plus Dataset")
    print("=" * 60)
    
    # Load dataset
    with open(DATASET_FILE) as f:
        dataset = json.load(f)
    
    # Sample SAMPLE_SIZE pairs
    sample = random.sample(dataset, min(SAMPLE_SIZE, len(dataset)))
    print(f"Using {len(sample)} samples from expanded dataset")
    
    results = []
    errors = 0
    
    for i, item in enumerate(sample):
        if (i + 1) % 25 == 0:
            print(f"  Progress: {i+1}/{len(sample)} | Errors: {errors}")
        
        response = query_model(item["claim"], item["evidence"])
        
        results.append({
            "pmid": item.get("pmid", ""),
            "claim": item["claim"],
            "evidence": item["evidence"],
            "true_label": item["label"],
            "predicted_label": response["label"],
            "confidence": response["confidence"],
            "action": response["action"],
            "rationale": response["rationale"],
        })
        
        time.sleep(0.3)  # Rate limit: ~3 req/sec on free Groq tier
    
    # Compute metrics
    metrics = compute_metrics(results)
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Accuracy:  {metrics['accuracy']}%")
    print(f"  SOCE:      {metrics['soce']:+.4f}")
    print(f"  CR:        {metrics['cr']}%")
    print(f"  PDEMC:     {metrics['pdemc']}")
    print("=" * 60)
    
    # Save
    output = {"model": MODEL, "metrics": metrics, "results": results}
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
