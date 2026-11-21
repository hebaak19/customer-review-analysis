"""Validate customer review submissions, append them to a results file and look up the product catalogue."""
import csv
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from review_analysis.config import NEGATIVE, NEGATIVE_MAX, NEUTRAL, POSITIVE, POSITIVE_MIN

logger = logging.getLogger(__name__)

PRODUCT_COL = "Clothing ID"
DEPARTMENT_COL = "Department Name"
CLASS_COL = "Class Name"
UNKNOWN = "Unknown"
MAX_REVIEW_CHARS = 5000
VALID_RATINGS = (1, 2, 3, 4, 5)

FIELDS = [
    "submitted_at",
    "product_id",
    "department",
    "class_name",
    "review_text",
    "rating",
    "predicted_sentiment",
    "confidence",
    "llm_issues",
    "llm_evidence",
    "llm_status",
]

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_WRITE_LOCK = threading.Lock()


class SubmissionError(Exception):
    """A submission is invalid, or the product catalogue or results file cannot be used."""


def load_product_catalog(path):
    """Return the distinct products with their department and class, read from the processed reviews."""
    path = Path(path)
    if not path.is_file():
        raise SubmissionError(f"Product list not found: {path}. Run scripts/run_pipeline.py first.")
    try:
        data = pd.read_csv(path, usecols=[PRODUCT_COL, DEPARTMENT_COL, CLASS_COL])
    except (ValueError, pd.errors.ParserError) as e:
        raise SubmissionError(f"Could not read the product list from {path}: {e}") from e
    data = data.dropna().drop_duplicates()
    data = data[(data[DEPARTMENT_COL] != UNKNOWN) & (data[CLASS_COL] != UNKNOWN)]
    if data.empty:
        raise SubmissionError(f"No products found in {path}.")
    return data.reset_index(drop=True)


def validate_submission(product_id, rating, text):
    """Raise SubmissionError if the product, rating or review text is not acceptable."""
    if product_id is None:
        raise SubmissionError("Please choose a product.")
    if rating not in VALID_RATINGS:
        raise SubmissionError("Please choose a rating from 1 to 5.")
    if not str(text or "").strip():
        raise SubmissionError("Please write a review before submitting.")
    if len(text) > MAX_REVIEW_CHARS:
        raise SubmissionError(f"The review is too long ({len(text):,} characters). The limit is {MAX_REVIEW_CHARS:,}.")


def _safe_cell(value):
    """Prefix text that a spreadsheet would run as a formula so it is shown as plain text instead."""
    text = str(value)
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


def build_record(product_id, department, class_name, rating, text, sentiment, confidence, issues, evidence, status):
    """Return one submission as a dictionary keyed by the results-file columns."""
    return {
        "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "product_id": int(product_id),
        "department": department,
        "class_name": class_name,
        "review_text": _safe_cell(text.strip()),
        "rating": int(rating),
        "predicted_sentiment": sentiment,
        "confidence": round(float(confidence), 3),
        "llm_issues": "|".join(issues),
        "llm_evidence": _safe_cell(evidence or ""),
        "llm_status": _safe_cell(status),
    }


def append_submission(path, record):
    """Append one submission to the results file, creating the file and header on first use."""
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _WRITE_LOCK:
            is_new = not path.is_file() or path.stat().st_size == 0
            with path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                if is_new:
                    writer.writeheader()
                writer.writerow(record)
    except PermissionError as e:
        raise SubmissionError(f"Could not write to {path}. Close it if it is open in another program.") from e
    except OSError as e:
        raise SubmissionError(f"Could not write to {path}: {e}") from e
    logger.info("Saved submission for product %s to %s", record["product_id"], path)


def rating_to_sentiment(rating):
    """Map a 1-5 star rating to negative, neutral or positive with the project's label thresholds."""
    if rating <= NEGATIVE_MAX:
        return NEGATIVE
    return POSITIVE if rating >= POSITIVE_MIN else NEUTRAL


def _restore_cell(value):
    """Undo the formula-protection prefix added by _safe_cell so the text is shown as the customer wrote it."""
    text = str(value)
    return text[1:] if len(text) > 1 and text[0] == "'" and text[1] in _FORMULA_PREFIXES else text


def submissions_as_issue_rows(frame):
    """Convert saved submissions to the row format of the LLM issue-extraction results."""
    ok = frame["llm_status"].fillna("") == "ok"
    return pd.DataFrame(
        {
            "review": frame["review_text"].map(_restore_cell),
            "Rating": frame["rating"],
            "sentiment": frame["rating"].map(rating_to_sentiment),
            DEPARTMENT_COL: frame["department"],
            CLASS_COL: frame["class_name"],
            "issues": frame["llm_issues"].fillna(""),
            "evidence": frame["llm_evidence"].fillna("").map(_restore_cell),
            "error": frame["llm_status"].where(~ok),
        }
    )
