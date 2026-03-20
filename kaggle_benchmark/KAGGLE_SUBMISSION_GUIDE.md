# SOEA-Plus Kaggle Submission Guide
## Step-by-Step: From Notebook to Benchmark to Writeup

---

## Overview

The competition requires **3 things**:
1. A **Kaggle Benchmark** (built with SDK) — *mandatory*
2. A **Kaggle Writeup** (your project report) — *mandatory*
3. A **Cover Image** in Media Gallery — *mandatory to submit*

---

## Step 1: Upload the Dataset to Kaggle

Before creating the benchmark notebook, upload the dataset.

1. Go to: https://www.kaggle.com/datasets/new
2. Click **"New Dataset"**
3. Upload `SOEA_300_gold_FINAL.csv`
4. Name it: `soea-plus-dataset`
5. Set visibility: **Private** (will auto-publish after deadline)
6. Click **Create**

Note the dataset URL: `https://www.kaggle.com/datasets/haifawaeedd/soea-plus-dataset`

---

## Step 2: Create the Benchmark Notebook

1. Go to: https://www.kaggle.com/benchmarks/tasks/new
   - This creates a new notebook with kaggle-benchmarks pre-installed

2. **Delete all existing cells** in the new notebook

3. **Upload the notebook file:**
   - Click the notebook menu (⋮) → "Import Notebook"
   - Upload `SOEA_Plus_PDEMC_Benchmark.ipynb`
   - OR copy-paste the code cells manually

4. **Add the dataset as input:**
   - In the right panel, click "Add data"
   - Search for `soea-plus-dataset`
   - Add it to the notebook

5. **Run the notebook:**
   - Click "Run All" (or Shift+Enter through each cell)
   - The benchmark will evaluate all 300 examples
   - This uses your Kaggle quota ($50/day provided by competition)

6. **Save a Version:**
   - Click "Save Version" → "Save & Run All (Commit)"
   - Wait for the run to complete

7. **Select the main task:**
   - The last cell contains `%choose soea_plus_pdemc`
   - This designates the PDEMC task as the benchmark's main metric

8. **Publish the benchmark:**
   - After saving, go to the benchmark page
   - Click "Publish" to create the Kaggle Benchmark entity
   - Note the benchmark URL

---

## Step 3: Create the Kaggle Writeup

1. Go to: https://www.kaggle.com/competitions/kaggle-measuring-agi/writeups
2. Click **"New Writeup"**

3. **Fill in the details:**
   - **Title:** `SOEA-Plus (PDEMC): The Control Collapse Hypothesis`
   - **Subtitle:** `Post-Decisional Metacognitive Control Benchmark for Medical LLMs`
   - **Track:** Select **"Metacognition"**

4. **Paste the writeup content:**
   - Copy the full content of `SOEA_PLUS_COMPETITION_WRITEUP.md`
   - Paste into the writeup editor

5. **Add Media Gallery (Cover Image required):**
   - Click "Media Gallery"
   - Upload `soea_plus_control_collapse.png` as the **cover image**
   - Also upload: `soea_plus_dashboard.png`, `soea_plus_architecture.png`

6. **Add Project Link (Benchmark — MANDATORY):**
   - Click "Attachments" → "Add a link"
   - Select your Kaggle Benchmark from the dropdown
   - This links your benchmark to the writeup

7. **Add GitHub link:**
   - Add another link: `https://github.com/Haifawaeedd/SOEA-Benchmark`
   - Label: "GitHub Repository"

8. **Save the writeup**

---

## Step 4: Submit

1. After saving the writeup, click **"Submit"** (top right corner)
2. Confirm submission
3. ✅ Done!

---

## Important Notes

- **Deadline:** Check the competition timeline page
- **One submission only** per team
- Tasks and benchmark are **private until deadline**, then auto-published
- The `%choose soea_plus_pdemc` magic command is critical — it tells Kaggle which task to use for the leaderboard

---

## File Checklist

| File | Status |
|------|--------|
| `SOEA_Plus_PDEMC_Benchmark.ipynb` | ✅ Ready |
| `SOEA_300_gold_FINAL.csv` | ✅ In `/data/` folder |
| `SOEA_PLUS_COMPETITION_WRITEUP.md` | ✅ Ready |
| `soea_plus_control_collapse.png` | ✅ Cover image |
| `soea_plus_dashboard.png` | ✅ Gallery image |
| `soea_plus_architecture.png` | ✅ Gallery image |

---

## Competition Link

https://www.kaggle.com/competitions/kaggle-measuring-agi
