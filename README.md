# Customer Review Analysis

An AI-based system that analyzes customer reviews and classifies them as **positive**, **negative**, or **neutral**. It helps businesses understand customer opinions, identify common issues, and improve customer support and services.

> ARTI303 | Programming for Artificial Intelligence - Final Project  
> Topic: **Customer Support - Customer Review Analysis**

> **Status:** project skeleton only. The folder structure is in place; the code, tests and app are not written yet. Sections marked *(planned)* describe the intended design.

## Table of contents
1. [Problem definition](#problem-definition)
2. [Dataset](#dataset)
3. [Workflow](#workflow-planned)
4. [AI method and evaluation](#ai-method-and-evaluation-planned)
5. [Streamlit app](#streamlit-app-planned)
6. [Project structure](#project-structure)
7. [Setup and usage](#setup-and-usage-planned)
8. [Limitations](#limitations)
9. [AI usage and acknowledgements](#ai-usage-and-acknowledgements)
10. [Team](#team)

## Problem definition
- **Target user:** customer-support and product teams at online retailers.
- **Problem:** thousands of free-text reviews arrive, and reading them by hand to find unhappy customers and recurring complaints does not scale.
- **Objectives:**
  - Classify each review as positive, negative, or neutral.
  - Surface the most common issues in negative reviews.
  - Show which product categories attract the most complaints.
- **Input:** a CSV of customer reviews (review text and star rating) or a single pasted review.
- **Output:** a sentiment label with confidence, summary charts, a list of frequent complaint terms, and downloadable predictions.
- **Why AI:** keyword rules miss context and phrasing variety. A trained text classifier generalizes across wording and produces measurable accuracy.
- **Existing solutions:** to be compared in the report (e.g. rule-based/lexicon tools, commercial sentiment APIs, review-analytics platforms).

## Dataset
**Women's E-Commerce Clothing Reviews** by nicapotato, on Kaggle  
https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews

| | |
|---|---|
| Size | about 23,486 reviews, 10 feature columns |
| Key columns | `Title`, `Review Text`, `Rating` (1-5), `Recommended IND`, `Class Name`, `Department Name` |
| License | CC0: Public Domain (per the Kaggle dataset page) |
| Privacy | described as anonymous; no reviewer names |

**Sentiment labels** are derived from star ratings: 1-2 stars = negative, 3 = neutral, 4-5 = positive.

**Download:** Kaggle needs a free account. Download the CSV from the dataset page and place it in `data/raw/`. The file is not committed to the repository.

## Workflow *(planned)*
Load -> Validate -> Clean -> Explore -> Visualize -> Transform -> Export -> Summary

| Step | What happens |
|---|---|
| Load | Read the CSV, handle missing or unreadable files |
| Validate | Check required columns, rating range, empty text, duplicates |
| Clean | Normalise text, drop unusable rows, merge title and body |
| Explore | Class balance, rating and review-length statistics |
| Visualize | Sentiment distribution, review length by sentiment, negative share per category |
| Transform | Map ratings to sentiment labels, build text features |
| Export | Save the cleaned dataset and trained model |
| Summary | Write metrics and findings to a report file |

## AI method and evaluation *(planned)*
- **Task:** three-class text classification.
- **Baseline:** TF-IDF features with a linear classifier (e.g. logistic regression), using class weighting because most reviews are positive. A pretrained model could be added if its role is explained.
- **Evaluation:** stratified train/test split; accuracy, macro-F1, per-class precision and recall, confusion matrix, and a qualitative review of misclassified examples.
- **Issue analysis:** frequent terms in negative reviews and negative-review share by product category.

## Streamlit app *(planned)*
- Paste a single review and see the predicted sentiment with confidence.
- Upload a CSV for batch analysis, charts and downloadable predictions.
- Clear error messages for empty input, wrong columns or unreadable files.

## Project structure
```
customer-review-analysis/
├── config/              configuration files
├── data/
│   ├── raw/             original dataset (not committed)
│   └── processed/       cleaned data (not committed)
├── docs/                report, AI usage report
├── logs/                run logs (not committed)
├── models/              trained models (not committed)
├── outputs/             figures and summaries (not committed)
├── scripts/             command-line entry points
├── src/review_analysis/ reusable modules
├── tests/               tests and small sample data
├── README.md
└── .gitignore
```

## Setup and usage
Run all commands from the project root. Requires Python 3.10 or newer.

**1. Create and activate a virtual environment, then install the packages**

| | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Create | `python -m venv .venv` | `python3 -m venv .venv` |
| Activate | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Install | `pip install -r requirements.txt` | `pip install -r requirements.txt` |

**2. Add the dataset.** Download it from Kaggle (see [Dataset](#dataset)) and save it as `data/raw/reviews.csv`. The name is case-sensitive on macOS and Linux.

**3. Run the preprocessing pipeline**

| Windows | macOS / Linux |
|---|---|
| `python scripts/run_pipeline.py` | `python3 scripts/run_pipeline.py` |

It loads, validates, cleans and labels the data, then writes `data/processed/clean_reviews.csv` and `outputs/reports/preprocessing_summary.json`. Use `--input` and `--output` to override the paths.

**Configuration:** paths, column names and thresholds are in `config/config.example.yaml`. To use personal settings, copy it to `config/config.yaml` (git-ignored). Write paths with forward slashes (`data/raw/reviews.csv`) and keep them relative to the project root.

*Planned:* model training, the Streamlit app (`streamlit run app.py`) and the tests (`pytest`).

## Limitations
- One domain (women's clothing), so results may not transfer to other products or to support tickets.
- Reviews are heavily skewed positive, so neutral and negative classes are small.
- Star ratings are a proxy for sentiment; some 3-star reviews read as clearly positive or negative.
- A bag-of-words model does not handle sarcasm or negation well.
- English only.

## AI usage and acknowledgements
Generative AI tools (Claude Code) assisted with dataset research and project setup. All use will be logged in `docs/AI_USAGE_REPORT.md` with prompts, verification and corrections, as the course requires. The dataset is credited to its Kaggle author (see [Dataset](#dataset)).

## Team
*Add group members and individual contributions here.*
