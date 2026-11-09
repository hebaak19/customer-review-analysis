"""Preprocessing: Load -> Validate -> Clean -> Transform -> Export -> Summary."""
import logging
import re
from pathlib import Path
from review_analysis.config import (
    TITLE_COL,
    TEXT_COL,
    RATING_COL,
    CATEGORY_COLS,
    NEGATIVE_MAX,
    POSITIVE_MIN,
    MIN_TEXT_CHARS,
    VALID_RATING_RANGE,
    MISSING_VALUE_PLACEHOLDER
)
import pandas as pd

from review_analysis.eda import build_eda_summary

logger = logging.getLogger(__name__)

_URL = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE = re.compile(r"\s+")


class DataLoadError(Exception):
    """The data file is missing or cannot be read."""


class DataValidationError(Exception):
    """The data does not have the required structure."""


class DataExportError(Exception):
    """The processed data could not be written."""


def load_data(file_path):
    """Read the CSV and drop any unnamed index column. Raises DataLoadError on failure."""
    path = Path(file_path)
    if not path.is_file():
        raise DataLoadError(f"File not found: {path}")
    try:
        data = pd.read_csv(path)
    except pd.errors.EmptyDataError as e:
        raise DataLoadError(f"The file is empty: {path}") from e
    except (pd.errors.ParserError, UnicodeDecodeError) as e:
        raise DataLoadError(f"Could not parse {path} as CSV: {e}") from e

    unnamed = [c for c in data.columns if str(c).startswith("Unnamed")]
    data = data.drop(columns=unnamed)
    logger.info("Data loaded successfully. Shape: %s", data.shape)
    return data


def validate_data(data):
    """Check structure and data quality.

    Raises DataValidationError for fatal problems (no data, missing required columns).
    Returns a dict with the counts of non-fatal problems, and logs them.
    """
    if data is None:
        raise DataValidationError("Data is None. Cannot validate.")
    if data.empty:
        raise DataValidationError("Dataframe is empty.")
    for col in (TEXT_COL, RATING_COL):
        if col not in data.columns:
            raise DataValidationError(f"Missing required column: {col}")

    ratings = pd.to_numeric(data[RATING_COL], errors="coerce")
    empty_text = data[TEXT_COL].fillna("").astype(str).str.strip() == ""
    report = {
        "rows": len(data),
        "missing_titles": int(data[TITLE_COL].isnull().sum()) if TITLE_COL in data.columns else 0,
        "missing_review_text": int(empty_text.sum()),
        "invalid_ratings": int((~ratings.isin(VALID_RATING_RANGE)).sum()),
        "duplicate_rows": int(data.duplicated().sum()),
        "missing_by_column": {c: int(n) for c, n in data.isnull().sum().items() if n > 0},
    }
    logger.info("Validation report: %s", report)
    return report


def _normalise_text(value):
    """Remove URLs and collapse whitespace."""
    if pd.isna(value):
        return ""
    return _WHITESPACE.sub(" ", _URL.sub(" ", str(value))).strip()


def clean_data(data):
    """Return (cleaned copy, dict of rows dropped per reason). The input is not modified.

    Only rows that cannot be used for classification are dropped (invalid rating,
    empty review text, duplicates). Missing titles/categories do NOT cause a row to be dropped.
    """
    if data is None:
        raise DataValidationError("Data is None. Cannot clean.")
    df = data.copy()
    dropped = {}

    
    df[RATING_COL] = pd.to_numeric(df[RATING_COL], errors="coerce")
    valid_rating = df[RATING_COL].isin(VALID_RATING_RANGE)
    dropped["invalid_rating"] = int((~valid_rating).sum())
    df = df[valid_rating].copy()
    df[RATING_COL] = df[RATING_COL].astype(int)

    
    df[TEXT_COL] = df[TEXT_COL].map(_normalise_text)
    has_text = df[TEXT_COL].str.len() >= MIN_TEXT_CHARS
    dropped["empty_text"] = int((~has_text).sum())
    df = df[has_text].copy()

    
    if TITLE_COL in df.columns:
        title = df[TITLE_COL].map(_normalise_text)
    else:
        title = pd.Series("", index=df.index)
    df["review"] = (title + ". " + df[TEXT_COL]).where(title != "", df[TEXT_COL])

    
    for col in CATEGORY_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(MISSING_VALUE_PLACEHOLDER)

    
    before = len(df)
    df = df.drop_duplicates(subset=["review", RATING_COL])
    dropped["duplicates"] = before - len(df)

    df = df.reset_index(drop=True)
    df["word_count"] = df["review"].str.split().str.len()
    logger.info("Data cleaned. Rows %d -> %d. Dropped: %s", len(data), len(df), dropped)
    return df, dropped


def _rating_to_sentiment(rating):
    if rating <= NEGATIVE_MAX:
        return "negative"
    if rating >= POSITIVE_MIN:
        return "positive"
    return "neutral"


def add_sentiment_labels(data):
    """Return a copy with a `sentiment` column derived from the rating."""
    if data is None:
        raise DataValidationError("No data to add sentiment labels.")
    if data[RATING_COL].isnull().any():
        raise DataValidationError("Ratings contain missing values; run clean_data first.")
    df = data.copy()
    df["sentiment"] = df[RATING_COL].map(_rating_to_sentiment)
    logger.info("Sentiment labels added: %s", df["sentiment"].value_counts().to_dict())
    return df


def export_data(data, output_path):
    """Write the data to CSV, creating the folder if needed. Raises DataExportError on failure."""
    if data is None:
        raise DataExportError("No data to export.")
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(path, index=False)
    except OSError as e:
        raise DataExportError(f"Could not write {path}: {e}") from e
    logger.info("Data exported successfully to %s", path)
    return path


def build_summary(raw_data, cleaned_data, dropped, validation_report=None):
    """Counts before and after, rows dropped by reason, and the label distribution."""
    summary = {
        "rows_before": len(raw_data),
        "rows_after": len(cleaned_data),
        "dropped_by_reason": dropped,
        "label_distribution": cleaned_data["sentiment"].value_counts().to_dict(),
        "validation": validation_report,
    }
    logger.info("Summary built: %s", summary)
    return summary


def preprocess_pipeline(input_path, output_path):
    """Run the full preprocessing pipeline and return the summary."""
    raw = load_data(input_path)
    report = validate_data(raw)
    cleaned, dropped = clean_data(raw)
    labeled = add_sentiment_labels(cleaned)
    export_data(labeled, output_path)
    summary = build_summary(raw, labeled, dropped, report)
    summary["eda"] = build_eda_summary(labeled)  # Explore step results, saved with the summary
    return summary
