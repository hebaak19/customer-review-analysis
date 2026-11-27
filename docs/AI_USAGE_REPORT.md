# AI Usage Report

ARTI303 Final Project - Customer Review Analysis.

> **How this draft was made.** The prompt log and the verification notes were rebuilt from the saved Claude Code session transcripts of this project (9 to 26 November 2026) and from the git history. Prompts are summarised or shortened, but none are invented.

## Contents
1. [Tools used](#1-tools-used)
2. [Project steps](#2-project-steps): Step 1 dataset, Step 2 data processing, Step 3 AI model, Step 4 Streamlit app, Step 5 automated tests
3. [Checks used across all steps](#3-checks-used-across-all-steps)
4. [Verification still outstanding](#4-verification-still-outstanding)
5. [Acknowledgements](#5-acknowledgements)

## 1. Tools used

| Tool | Version / model | Used for |
|---|---|---|
| Claude Code (Anthropic CLI agent) | Model name: Claude Sonnet 5.5 | Dataset search, EDA, model training, the app, tests, documentation |
| Claude in Chrome / Playwright MCP | Browser tools inside Claude Code | Browsing Kaggle and Hugging Face to compare datasets, and visually checking the Streamlit pages |
| DeepSeek-V4.1-Flash via the Fuse API | Hosted model, called through an API | **Product component, not a development aid.** It extracts complaint categories from reviews. See the README section "AI method and evaluation". |
| Pylint | Static checker, run once by Claude Code | Style and error check of `src` and `scripts` |

No other generative AI tool (ChatGPT, Copilot, Gemini and so on) is recorded in the transcripts.

## 2. Project steps

Each step has the same layout: what the step was for, the prompts the team gave and what the AI produced, and then the mistakes and bugs found in that step with how they were corrected.

---

### Step 1 - Find the dataset (9 Nov)

**Goal:** choose a public dataset that fits the guidelines.

**How the dataset was found.** The team asked Claude Code to find a dataset for "AI for Customer Support - Customer Review Analysis" using the Playwright MCP, and registered it with `claude mcp add playwright -- npx -y @playwright/mcp@latest`. That server only loads after Claude Code is restarted, so the first search ran through the Claude in Chrome browser tools instead.

| Stage | What happened |
|---|---|
| 1. Hugging Face | The long description found nothing, so a shorter query was used. The page showed one result at a time, so Hugging Face's public search API was queried for a fuller list. The best match was `Yelp/yelp_review_full` (650,000 training reviews, labels 1 to 5 stars). |
| 2. Kaggle | The team asked for Kaggle too. The search "customer reviews sentiment" returned 592 datasets, and the AI opened the two strongest candidates, *Women's E-Commerce Clothing Reviews* and *Amazon Reviews for Sentiment Analysis*. |
| 3. Comparison | The AI compared size, labels, text length and licence across the three. |
| 4. Guidelines check | The team asked the AI to read the project guidelines first. They prefer Kaggle, require a cited URL and licence, and require no personal data. Yelp's licence is restrictive, and the Kaggle clothing dataset is CC0. |
| 5. Decision (team) | The team chose *Women's E-Commerce Clothing Reviews* and downloaded the CSV themselves, because Kaggle needs a login. Its URL, licence and limitations are in the README. |

**Prompts and AI output**

| # | Prompt | What the AI produced |
|---|---|---|
| 1 | Use the browser to find a customer-review dataset on Hugging Face or Kaggle | Found `Yelp/yelp_review_full` and recommended it |
| 2 | Search Kaggle too and compare with Yelp | Comparison table of Yelp, Women's E-Commerce Clothing Reviews and Amazon Reviews |
| 3 | Check the guidelines first | Read the PDF and listed the dataset requirements (public source, cited licence, no personal data). Yelp's restrictive licence was flagged as a risk. |

---

### Step 2 - Data processing and exploration (9 and 13 Nov)

**Goal:** Load, validate, clean, explore, visualize, transform and export the data (`preprocessing.py`, `eda.py`, `visualization.py`, the config file and the scripts).

**Prompts and AI output**

| # | Prompt | What the AI produced |
|---|---|---|
| 4 | Help write a preprocessing module using the required workflow, "don't write any code" | A written design only; the team wrote the code themselves |
| 5 | Add the EDA results to JSON and fix the requirements |

**Corrections in this step**

| What went wrong | How it was found | Correction |
|---|---|---|
| `config.py` was overwritten without being read first | The AI reported it in its own summary | The constants the team's code needed were restored from the imports, and the pipeline was re-run to confirm identical output (22,636 rows) |
| `plot_category_sentiment_distribution` crashed on a missing pandas import and plotted the extra `total` and percentage columns as classes | Run on the cleaned data | Import added, extra columns removed, the function returns a figure instead of calling `plt.show()` |
| `plot_rating_distribution` used the wrong default column name and failed on every call | Run on the cleaned data | The default now comes from the config (`RATING_COL`) |

---

### Step 3 - AI model: sentiment classifier and complaint extraction (13 to 21 Nov)

**Goal:** a trained sentiment model plus a language model that extracts complaints, with evaluation evidence.

**Prompts and AI output**

| # | Prompt | What the AI produced |
|---|---|---|
| 6 | Use the Fuse API key from `.env`; choose the best model for our project | `llm.py`, `scripts/benchmark_llm.py`; benchmark of four models; DeepSeek-V4.1-Flash recommended |

**Corrections in this step**

| What went wrong | How it was found | Correction |
|---|---|---|
| The first benchmark used a balanced 90-review sample, which inflated the LLM's advantage | Team asked whether the balanced sample created bias | Reweighting and a 600-review natural-mix benchmark were run. The two models turned out to be tied, so the LLM was kept only for complaint extraction. |
| The whole dataset (about 22,600 reviews) was sent to the paid LLM API without checking the scale with the team | Team asked "why are you sending the whole dataset, just send a test sample" | Run stopped between batches; a 2,000-review random sample with a fixed seed was kept and `llm.max_reviews` now caps every run |
| The resume logic of complaint extraction marked failed reviews as done, so they were never retried | AI found it while running the extraction | Failed reviews are now retried on the next run |
| About 1 LLM reply in 50 was unparseable | 50-review trial run | Extraction retries once |

---

### Step 4 - Streamlit app (21 Nov)

**Goal:** an interactive app that shows the results and lets a customer write a review that is analysed and saved.

**Prompts and AI output**

| # | Prompt | What the AI produced |
|---|---|---|
| 7 | Build the app on a new branch; put the web app inside `src` | `app.py` and `src/webapp/` with four pages |
| 8 | The numbers are misleading; say whether they come from the LLM or our model; use colours or sections instead | Colour-coded sources: mulberry, blue and amber |

**Corrections in this step**

| What went wrong | How it was found | Correction |
|---|---|---|
| UI figures said "AI" for everything and were misleading | Team said the numbers were misleading | Every figure and chart is now labelled and colour-coded as language model, trained model or star rating |
| The page was not mobile responsive; the Deploy button disappeared | Team reported both | Responsive CSS added and checked at 390 px; the AI explained that its own toolbar-hiding setting removed the button |

### Step 5 - Automated tests (26 Nov)

**Goal:** a pytest suite that checks the analysis code on a small synthetic file, so it needs no dataset download and no API key.

**Prompts and AI output**

| # | Prompt | What the AI produced |
|---|---|---|
| 9 | Check our existing code against the project guidelines PDF for any missing folder, file or task | A list of gaps, one of which was that the project had no automated tests |
| 10 | "Tests plus a small sample CSV" (chosen from that list) | `tests/data/sample_reviews.csv` (37 synthetic rows with the Kaggle columns, including an invalid rating, empty text, a duplicate, a missing title and a URL), `tests/conftest.py` and four test files (`test_preprocessing.py`, `test_modeling.py`, `test_submissions.py`, `test_issues.py`) with 69 tests. `pytest==9.2.0` was installed in the venv and added to `requirements.txt`, and the README gained a "run the tests" step. |

**How the AI wrote them.** It first read the source modules (`preprocessing.py`, `modeling.py`, `submissions.py`, `issue_extraction.py`, `llm.py`, `insights.py`) to see each function's inputs, outputs and errors. It then wrote tests for the normal case and for the edge cases, such as missing or empty files, bad ratings, corrupt model files and malformed language-model replies. The language-model API is not called by any test.

**Corrections in this step**

| What went wrong | How it was found | Correction |
|---|---|---|
| The first attempt to create the files through a shell heredoc wrote nothing | The AI listed the folder afterwards and found it unchanged | The files were created again with the file-writing tool |
| The AI miscounted the sample file: the tests expected 36 rows, and the file has 37 | The first test run failed on the row counts | The expected totals were changed to 37 before cleaning and 34 after |
| `requirements.txt` was saved as UTF-16, which made it hard to edit and diff | Found while adding `pytest` | The file was re-saved as UTF-8 |

---

## 3. Checks used across all steps

- Each code change was run on the real dataset (23,486 rows in, 22,636 out) and the counts were compared with the earlier run.
- The model's headline numbers were checked against baselines: majority class macro-F1 0.290 against TF-IDF 0.657 on a held-out stratified test set of 4,528 reviews.
- Streamlit pages were tested headlessly and checked by eye in a real browser, including at phone width (390 px).
- Commits were scanned for secrets, data files and model files before pushing.
- 69 automated pytest tests (Step 5) cover preprocessing, the model, evaluation, submissions and complaint parsing. They passed on the AI's run (about 3 seconds) and the team has also run them.
- Claims in the README were corrected when they overstated results (for example the claim that the LLM beats the trained model on neutral reviews).

## 4. Verification still outstanding

- The LLM's complaint labels have **not** been checked against human judgement. The complaint rate they produce looks high and may include minor remarks, so complaint figures are indicative only. The README lists this under Limitations.
- The Streamlit pages are not covered by automated tests. They were checked with headless runs and by hand in a browser.
- Neutral reviews are the weak class of the sentiment model (F1 0.455 on the full test set). Three language models and the trained model all score about 0.3 to 0.45 on neutral, so the limit is the star-rating labels, not the models.
- The language-model comparison uses 600 and 90 reviews, so small differences between models are noise.
- This log covers the Claude Code sessions run in this repository folder. No other AI tool is recorded.

## 5. Acknowledgements

- Dataset: *Women's E-Commerce Clothing Reviews* by nicapotato, Kaggle, CC0 Public Domain.
- Libraries: pandas, NumPy, scikit-learn, matplotlib, seaborn, Streamlit, joblib, PyYAML and pytest.
- Language model: DeepSeek-V4.1-Flash through the Fuse API, used as a component of the product.
- Code and documentation assistance: Claude Code, as described above.
