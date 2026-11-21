# Customer Review Analysis

An AI system for women's clothing retailers that reads customer reviews and answers two questions: **how does the customer feel** (positive, neutral or negative), and **what went wrong** (fit, sizing, fabric, quality and more). A Streamlit app shows the results and lets customers write new reviews, which are analysed and saved.

> ARTI303 | Programming for Artificial Intelligence - Final Project  
> Topic: **Customer Support - Customer Review Analysis**

> **Status:** working prototype. The data pipeline, the sentiment model, the LLM complaint extraction and the Streamlit app are implemented. There is no automated test suite yet, and the LLM's complaint labels have not been checked by hand (see [Limitations](#limitations)).

## Table of contents
1. [Problem definition](#problem-definition)
2. [Dataset](#dataset)
3. [Workflow](#workflow)
4. [AI method and evaluation](#ai-method-and-evaluation)
5. [Streamlit app](#streamlit-app)
6. [Project structure](#project-structure)
7. [Setup and usage](#setup-and-usage)
8. [Limitations](#limitations)
9. [AI usage and acknowledgements](#ai-usage-and-acknowledgements)
10. [Team](#team)

## Problem definition
- **Target user:** customer-support and product teams at online fashion retailers, and the customers who write the reviews.
- **Problem:** thousands of free-text reviews arrive. Reading them by hand to find unhappy customers and recurring complaints does not scale, and star ratings alone do not say what went wrong.
- **Objectives:**
  - Classify each review as positive, neutral or negative.
  - Find what customers complain about, including complaints hidden inside positive reviews.
  - Show which departments and product classes attract the most complaints.
  - Let a customer write a review for a product and get it analysed and saved.
- **Input:** customer reviews (review text and star rating), or a single review written in the app.
- **Output:** a sentiment label with confidence, complaint categories with a quoted phrase as evidence, charts by department and product class, and a saved results file.
- **Why AI:** keyword rules miss context and phrasing variety. A trained classifier measures sentiment cheaply and offline. A language model reads free text and extracts structured complaints without any labelled complaint data.
- **Existing solutions:** to be compared in the report (for example lexicon tools, commercial sentiment APIs and review-analytics platforms).

## Dataset
**Women's E-Commerce Clothing Reviews** by nicapotato, on Kaggle  
https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews

| | |
|---|---|
| Size | about 23,486 reviews, 10 feature columns (22,636 after cleaning) |
| Key columns | `Title`, `Review Text`, `Rating` (1-5), `Recommended IND`, `Clothing ID`, `Class Name`, `Department Name` |
| License | CC0: Public Domain (per the Kaggle dataset page) |
| Privacy | described as anonymous; no reviewer names |

**Sentiment labels** are derived from star ratings: 1-2 stars = negative, 3 = neutral, 4-5 = positive. After cleaning, about 77% of reviews are positive, 12% neutral and 10% negative.

**Download:** Kaggle needs a free account. Download the CSV from the dataset page and save it as `data/raw/reviews.csv`.

## Workflow
```
raw reviews.csv
   |
   v
run_pipeline.py --> clean_reviews.csv
                       |                          |
                       v                          v
                train_model.py             extract_issues.py
        (TF-IDF sentiment classifier)   (language model reads each review)
                       |                          |
                       v                          v
         models/sentiment_model.joblib   outputs/reports/issue_extraction.csv
                       \                         /
                        v                       v
                         Streamlit app (app.py)
```

| Step | Script | What happens |
|---|---|---|
| Preprocess | `scripts/run_pipeline.py` | Load, validate, clean, label and export the data, plus an EDA summary |
| Explore | `scripts/visualize_data.py` | Charts of class balance, ratings and sentiment by category, saved as PNG files in `outputs/figures` |
| Train | `scripts/train_model.py` | Train and evaluate the sentiment model, save the model, metrics and misclassified reviews |
| Benchmark | `scripts/benchmark_llm.py` | Compare the language model with the trained model on a test sample |
| Extract | `scripts/extract_issues.py` | Language model lists the complaint categories in each review (capped, see below) |
| Serve | `app.py` | Streamlit app that reads the saved files and handles new reviews |

## AI method and evaluation
The project uses two models with clearly separate jobs.

| | Trained model | Language model |
|---|---|---|
| **What it is** | TF-IDF features and class-weighted logistic regression, trained here | DeepSeek-V4.1-Flash, called through the Fuse API (OpenAI-compatible) |
| **Job** | Sentiment: positive, neutral or negative, with a confidence | Complaint extraction: categories and a short evidence quote |
| **Runs** | Locally and instantly, inside the app | Offline in batches for the dataset, and live once per review submitted in the app |
| **Training** | Trained on 80% of the data with a stratified split | None. It follows a fixed prompt and a fixed list of categories |

### Sentiment model (trained)
Evaluated on a held-out, stratified test set of 4,528 reviews that the model never saw.

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Always predict the majority class | 0.771 | 0.290 |
| **TF-IDF + logistic regression** | **0.815** | **0.657** |

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Negative | 0.55 | 0.65 | 0.60 |
| Neutral | 0.39 | 0.54 | 0.45 |
| Positive | 0.96 | 0.88 | 0.92 |

Macro-F1 is the headline metric because accuracy alone is misleading when 77% of reviews are positive. Neutral is the weak class.

### Language model compared with the trained model
Both models were asked to label the same reviews. The language model was told the star-rating mapping (1-2 negative, 3 neutral, 4-5 positive) so it matches the labels.

| Sample | Model | Accuracy | Macro-F1 | Neutral F1 | Negative recall |
|---|---|---|---|---|---|
| 600 random test reviews (real class mix) | TF-IDF | 0.795 | 0.612 | 0.337 | 0.620 |
| | DeepSeek-V4.1-Flash | 0.792 | 0.629 | 0.321 | 0.831 |
| 90 reviews, 30 per class (balanced) | TF-IDF | 0.722 | 0.714 | 0.582 | 0.700 |
| | DeepSeek-V4.1-Flash | 0.811 | 0.803 | 0.653 | 0.967 |

How to read this:
- On the real class mix the two models are **tied overall**. The gap is inside the noise of a 600-review sample. The language model finds more negative reviews (recall 0.83 against 0.62) but is no better on neutral.
- The balanced sample **overstates the language model's advantage**. Equal class sizes inflate precision and macro-F1 compared with real use, so the random sample is the fairer comparison.
- Because the language model is no better at sentiment, the app keeps the trained model for sentiment and uses the language model for what it alone can do: extracting complaints from free text.

### Complaint extraction (language model)
Each review is sent to the language model with a fixed list of nine categories: fit, size, fabric, quality, color, price, comfort, service and other. It returns the categories that apply (none, one or several) and a short quote as evidence. Counts, percentages, charts and the Overview findings are then computed by ordinary code from those saved answers.

- Extraction is **capped at 2,000 reviews** (`llm.max_reviews` in the config), chosen at random with a fixed seed, so a run cannot send the whole dataset.
- A review that fails is retried on the next run.
- The labels have **not been checked against human judgement yet**. The complaint rate they produce looks high and may include minor remarks.

### Other things we tried
These are not in the code any more, but they shaped the design.

| Experiment | Result |
|---|---|
| Frozen sentence embeddings instead of TF-IDF | Worse alone (macro-F1 0.610). Combined with TF-IDF it was 0.662 against 0.657, which is inside the noise. Dropped. |
| Tuning `C`, shifting class thresholds, ordinal regression on the 1-5 rating | No gain. The model was not under-tuned. |
| Other language models (Qwen3.8-Flash-Next, Kimi-K3) | All were within about 0.02 macro-F1 of each other on the same 600 reviews. A fourth model ignored the one-word output format. |
| Fine-tuning a transformer | The script ran, but training on this laptop CPU would take hours, so it was removed. |

Three different language models that followed the output format, and the trained model, all score about 0.3 to 0.45 F1 on neutral. That points to the **labels**, not the models: a 3-star rating is not a distinct kind of review.

## Streamlit app
Run it with `streamlit run app.py`. The interface code lives in `src/webapp/`, separate from the analysis code in `src/review_analysis/`.

| Page | What it does |
|---|---|
| **Overview** | A headline finding computed from the data, key figures, a department-by-complaint heatmap and short findings |
| **Write a review** | The customer chooses a type of clothing, category and product ID, gives 1-5 stars and writes a review. The trained model scores sentiment and the language model finds complaints. The result is shown and appended to `data/submissions/review_submissions.csv`. If the language model is unavailable, the review is still saved with the failure noted. |
| **Complaints** | Filters, complaint charts by department and product class, and a searchable table of reviews with evidence quotes. It combines the dataset sample with reviews written in the app. |
| **AI performance** | The trained model's test results, confusion matrix, top words, the comparison with the language model, and the limits |

**Which model produced which number.** Every figure and section is colour-coded by source, with a key at the top of each page: mulberry for the **language model**, blue for the **trained model**, and amber for **customers' star ratings**. Screen readers get the source in text, so colour is never the only cue.

The app is built to be responsive and was checked at phone width (390 px) and on desktop. It never calls the language model while browsing. It makes one call per review that a customer submits.

The saved results file is created at runtime and is git-ignored. Text starting with a spreadsheet formula character is prefixed with a quote so the CSV is safe to open in Excel.

## Project structure
```
customer-review-analysis/
├── app.py                 Streamlit entry point
├── .streamlit/            app theme and display settings
├── config/                configuration (config.example.yaml)
├── data/
│   ├── raw/               original dataset (not committed)
│   ├── processed/         cleaned data (not committed)
│   └── submissions/       reviews written in the app (not committed)
├── docs/                  project plan, report, AI usage report
├── logs/                  run logs (not committed)
├── models/                trained model (not committed)
├── outputs/               figures and reports (not committed)
├── scripts/               command-line entry points
│   ├── run_pipeline.py        preprocessing
│   ├── visualize_data.py      exploratory charts
│   ├── train_model.py         train and evaluate the sentiment model
│   ├── benchmark_llm.py       language model against the trained model
│   └── extract_issues.py      complaint extraction
├── src/
│   ├── review_analysis/   data, model and language-model logic (no UI code)
│   │   ├── preprocessing.py, eda.py, visualization.py
│   │   ├── modeling.py, evaluation.py
│   │   ├── llm.py, issue_extraction.py
│   │   └── insights.py, submissions.py
│   └── webapp/            Streamlit pages, charts and styling
├── tests/                 sample data (tests not written yet)
├── .env.example           names of the secrets the app needs
├── requirements.txt
└── README.md
```

## Setup and usage
Run all commands from the project root. Requires **Python 3.12 or newer** (developed on 3.13).

**1. Create and activate a virtual environment, then install the packages**

| | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Create | `python -m venv .venv` | `python3 -m venv .venv` |
| Activate | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Install | `pip install -r requirements.txt` | `pip install -r requirements.txt` |

**2. Add the dataset.** Download it from Kaggle (see [Dataset](#dataset)) and save it as `data/raw/reviews.csv`. The name is case-sensitive on macOS and Linux.

**3. Add your API key.** Copy `.env.example` to `.env` and fill in the two values. The file is git-ignored, so the key stays out of the repository.

```
FUSE_API_KEY=your-key-here
FUSE_BASE_URL=https://api.fuse.humainaic.com/v1
```

The key is only needed for complaint extraction, the benchmark and the live analysis in the Write a review page. Everything else runs without it.

**4. Build the data and the model.** These steps create files that are not committed, so every fresh clone must run them.

| Step | Windows | macOS / Linux |
|---|---|---|
| Preprocess | `python scripts/run_pipeline.py` | `python3 scripts/run_pipeline.py` |
| Train and evaluate | `python scripts/train_model.py` | `python3 scripts/train_model.py` |

Preprocessing writes `data/processed/clean_reviews.csv`. Training writes `models/sentiment_model.joblib` and the metrics in `outputs/reports/`.

**5. Create the complaint results (optional, uses the API).**

| Windows | macOS / Linux |
|---|---|
| `python scripts/extract_issues.py` | `python3 scripts/extract_issues.py` |

It analyses a random sample up to the `llm.max_reviews` cap (2,000 by default) and saves the answers batch by batch, so an interrupted run resumes. Use `--limit N` to change the cap for one run. `python scripts/benchmark_llm.py` reproduces the model comparison.

**6. Start the app**

```
streamlit run app.py
```

The first page load takes around 15 to 30 seconds while the model and libraries load. Without step 5, the Overview and Complaints pages show an empty state instead of data.

**Configuration:** paths, column names, model settings and the language-model settings are in `config/config.example.yaml`. To use personal settings, copy it to `config/config.yaml` (git-ignored). Write paths with forward slashes and keep them relative to the project root.

**Running it on a server.** A fresh deployment starts from the repository only, so the git-ignored files from steps 4 and 5 must be generated or committed first, the API key must be set in the host's secrets, and the submissions file is not persistent on most hosts. Anyone who can reach the app can trigger language-model calls with your key.

## Limitations
- **The complaint labels are unverified.** The language model decides which categories apply to each review. Its complaint rate is high, and part of that may be minor remarks. A hand-check against human judgement is still to be done.
- **Neutral is the weak class.** Every model that followed the output format scores about 0.3 to 0.45 F1 on neutral, because a 3-star rating does not correspond to a distinct kind of text.
- **Star ratings are a proxy for sentiment.** Some 3-star reviews read as clearly positive or negative.
- **Skewed classes.** About 77% of reviews are positive, so accuracy flatters the model and the negative and neutral classes are small.
- **The evaluation samples are small.** The language-model comparison uses 600 and 90 reviews, so small differences are noise.
- **One domain, English only.** Results may not transfer to other products or to support tickets.
- **A bag-of-words model** does not handle sarcasm or negation well.
- **Language-model output can vary between runs** and depends on an external service that can fail or change.
- **The complaint data is a 2,000-review sample**, not the whole dataset.
- **No automated tests yet.** The pages were checked with throw-away headless runs and by hand, but no test suite is committed.
- **Submissions are stored in a local CSV.** There is no database, no user accounts and no rate limit on the live analysis.

## AI usage and acknowledgements
Generative AI tools (Claude Code) assisted with dataset research, the data pipeline, the models, the app and its design, and this documentation. All use is to be logged in `docs/AI_USAGE_REPORT.md` with prompts, verification and corrections, as the course requires; that file has not been written yet. The language model DeepSeek-V4.1-Flash is also a **component of the product**: it reads reviews through the Fuse API as described above. The dataset is credited to its Kaggle author (see [Dataset](#dataset)).

## Team
*Add group members and individual contributions here.*
