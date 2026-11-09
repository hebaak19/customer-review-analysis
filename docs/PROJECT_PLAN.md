# Project Plan - Customer Review Analysis

ARTI303 Final Project (15 marks, group of 5). Deliverables: GitHub repo, project report (PDF), AI usage report, presentation, working Streamlit app.

> Deadlines, presentation length and group rules will be announced by the instructor. Phases below are ordered by dependency; add dates once they are known.

## 1. Team and roles

Replace the placeholders with real names. Each role has one **owner** who is accountable for the area; everyone reviews at least one other member's work.

| # | Member | Role | Owns |
|---|---|---|---|
| 1 | *Name* | **Project lead and documentation** | Topic registration, problem definition, repo setup, README, report assembly, presentation |
| 2 | *Name* | **Data engineer** | Load, validate, clean, export; configuration; logging |
| 3 | *Name* | **Analyst (EDA and issues)** | Exploration, visualizations, rating-to-sentiment transform, common-issue analysis |
| 4 | *Name* | **ML engineer** | Sentiment model, evaluation, error analysis, limitations |
| 5 | *Name* | **App and quality engineer** | Streamlit app, tests, reproducibility, requirements, sample data |

Every member must be able to explain their own work in the live demo, so each person also writes their own report section and presentation slides.

## 2. Task breakdown

### Member 1 - Project lead and documentation
- Register the group, title and proposal in the shared topic-selection sheet (**first-come, first-served, do this first**).
- Write the problem definition: target user, objectives, inputs/outputs, why AI, comparison with existing solutions.
- Create the GitHub repository, branch rules and issue board; keep `README.md` current.
- Collect and merge report sections; check the report against the required contents list.
- Build the presentation skeleton and run the rehearsal.
- Keep the master AI Usage Report and chase members for their entries.

### Member 2 - Data engineer
- Download the Kaggle dataset and document source URL, license (CC0) and limitations.
- Implement `Load -> Validate -> Clean -> Export` as reusable functions with exception handling and logging.
- Create the configuration file (paths, column names, thresholds) and a config example.
- Hand a cleaned dataframe with a documented schema to members 3 and 4.

### Member 3 - Analyst (EDA and issues)
- Explore the data: class balance, rating and review-length statistics, missing values.
- Produce the visualizations (sentiment distribution, review length by sentiment, negative share per category).
- Implement the rating-to-sentiment transform (1-2 negative, 3 neutral, 4-5 positive).
- Implement common-issue analysis: frequent terms in negative reviews, categories with most complaints.
- Write the report sections on processing steps and findings.

### Member 4 - ML engineer
- Build a baseline classifier (TF-IDF plus a linear model, class-weighted) with a stratified train/test split.
- Evaluate: accuracy, macro-F1, per-class precision/recall, confusion matrix.
- Do qualitative error analysis on misclassified reviews; discuss limitations (skewed classes, proxy labels, sarcasm).
- Optional stretch: compare with one more model or a pretrained model, explaining its role.
- Save and load the trained model for the app.

### Member 5 - App and quality engineer
- Build the Streamlit app: single-review prediction, CSV upload, charts, downloadable results, graceful handling of invalid input.
- Write the tests (cleaning, transform, model, edge cases) and a small **synthetic** sample dataset for demos and tests.
- Write `requirements.txt` and exact setup/run instructions; verify a fresh clone runs end to end.
- Take screenshots for the report and prepare the live-demo script.

### Shared by everyone
- Add your prompts, outputs and verification notes to the AI Usage Report as you go (not at the end).
- Write your own report section and presentation slides; list your individual contribution.
- Review at least one pull request from another member.

## 3. Phases

| Phase | Goal | Main owners | Done when |
|---|---|---|---|
| 0. Kickoff | Topic registered, roles agreed, repo and board created | 1 | Topic is in the sheet; everyone has repo access |
| 1. Data | Clean, validated dataset and config | 2 (with 3) | Cleaned data exported; schema documented |
| 2. Analysis and model | EDA, labels, issue analysis, trained and evaluated model | 3, 4 | Figures saved; metrics and error analysis written |
| 3. App and tests | Working Streamlit app and test suite | 5 (with 2, 4) | App runs from a fresh clone; tests pass |
| 4. Integration | Everything connected, README and setup verified | 1, 5 | A teammate who did not write the code can run it |
| 5. Reports and slides | Report, AI usage report, presentation | all | Documents checked against the guidelines |
| 6. Rehearsal and submission | Demo rehearsed; repo, report, slides submitted | 1 | Submission checklist complete |

Phases 2 and 3 can overlap once Phase 1 hands over the cleaned data. Member 5 can start the app shell with the sample data before the real model exists.

## 4. Interfaces between members

Agree these early so people can work in parallel:

- **Cleaned data schema:** a review text column (title and body combined), the numeric rating, the sentiment label, and the product category. Member 2 defines it; members 3, 4 and 5 depend on it.
- **Model interface:** train on a dataframe, return a model plus metrics; predict from a list of texts returning a label and probabilities. Member 4 defines it; member 5 uses it.
- **Config:** one place for paths, column names and thresholds, so nobody hard-codes them.

## 5. Working agreement

- **Git:** `main` stays working. Each person works on a branch (`feature/<area>-<name>`) and merges through a pull request with at least one review.
- **Commits:** small and frequent, with clear messages. No datasets, models or secrets in the repo.
- **Standups:** short check-in twice a week (chat is fine): done, next, blocked.
- **Definition of done for a task:** works, has error handling and logging where relevant, is documented, and is reviewed.
- **If someone is stuck for more than a day,** say so; the lead reassigns or pairs people.

## 6. Mapping to the grading rubric

| Rubric criterion (marks) | Main owners | Evidence |
|---|---|---|
| Problem definition and solution (2) | 1 | Problem section in report and README |
| Data processing and exploration (3) | 2, 3 | Cited data, validation, cleaning, EDA, charts, export |
| Python programming and code quality (3) | 2, 5 (all) | Modules, error handling, logging, config, docs, tests |
| AI implementation and evaluation (3) | 4 | Working model, metrics, error analysis, limitations |
| Streamlit application (2) | 5 | Interactive app with charts and invalid-input handling |
| Report, reproducibility, AI usage, presentation (2) | 1 (all) | Complete repo, report, AI usage log, slides, contributions |

## 7. Submission checklist

- [ ] Topic registered in the shared sheet
- [ ] GitHub repo: source code, entry point, reusable modules, `requirements.txt`, `README.md`, config example, sample data, tests
- [ ] Project report (PDF) with all required sections and individual contributions
- [ ] AI Usage Report (submitted even if no AI tools were used)
- [ ] Presentation (PPTX or PDF) including live demo, limitations and team contributions
- [ ] Streamlit app runs locally from a fresh clone using the README instructions
- [ ] Dataset, code, pretrained models and AI assistance all acknowledged

## 8. Risks

| Risk | Mitigation |
|---|---|
| Topic already taken | Register first; keep a backup topic ready |
| Kaggle download needs a login | One member downloads it and shares it with the team outside the repo; document the steps |
| Classes are imbalanced (few neutral and negative reviews) | Class weighting, macro-F1 as the main metric, discuss in limitations |
| Model accuracy is modest | Report it honestly with error analysis; the grading rewards sound evaluation, not a complex model |
| Members blocked on each other | Agree the interfaces early; use the sample data to work in parallel |
| Work piles up at the end | Keep AI usage entries and report sections up to date during each phase |
| Merge conflicts | Small branches, pull requests, one owner per module |
