"""Tests for review submission validation, storage and conversion."""
import pandas as pd
import pytest

from review_analysis import submissions as sub
from review_analysis.submissions import SubmissionError


def make_record(text="Great dress", status="ok"):
    """Return a valid submission record for the given text and status."""
    return sub.build_record(101, "Dresses", "Dresses", 5, text, "positive", 0.91234, ["fit"], "too tight", status)


def test_validate_accepts_good_input():
    """A product, rating and text pass validation."""
    sub.validate_submission(101, 5, "Lovely")


@pytest.mark.parametrize(
    "product,rating,text",
    [(None, 5, "ok"), (101, 0, "ok"), (101, 6, "ok"), (101, None, "ok"), (101, 5, ""), (101, 5, "   "), (101, 5, None)],
)
def test_validate_rejects_bad_input(product, rating, text):
    """Missing product, bad rating or blank text is rejected."""
    with pytest.raises(SubmissionError):
        sub.validate_submission(product, rating, text)


def test_validate_rejects_too_long_text():
    """Text over the limit is rejected."""
    with pytest.raises(SubmissionError):
        sub.validate_submission(101, 5, "x" * (sub.MAX_REVIEW_CHARS + 1))


def test_record_has_all_fields_and_rounds_confidence():
    """A record has every results column and a rounded confidence."""
    record = make_record()
    assert set(record) == set(sub.FIELDS)
    assert record["confidence"] == 0.912
    assert record["llm_issues"] == "fit"


@pytest.mark.parametrize("text", ["=1+1", "+cmd", "-5", "@SUM(A1)"])
def test_formula_text_is_protected(text):
    """Text that starts like a spreadsheet formula is prefixed with a quote."""
    assert make_record(text)["review_text"].startswith("'")


def test_append_creates_file_with_header_once(tmp_path):
    """The first append writes the header and later appends do not repeat it."""
    path = tmp_path / "out" / "subs.csv"
    sub.append_submission(path, make_record("first"))
    sub.append_submission(path, make_record("second"))
    frame = pd.read_csv(path)
    assert list(frame.columns) == sub.FIELDS
    assert len(frame) == 2


def test_rating_to_sentiment():
    """Ratings map to sentiment labels."""
    assert [sub.rating_to_sentiment(r) for r in (1, 2, 3, 4, 5)] == ["negative", "negative", "neutral", "positive", "positive"]


def test_saved_formula_text_round_trips(tmp_path):
    """Protected text is restored when submissions are converted to issue rows."""
    path = tmp_path / "subs.csv"
    sub.append_submission(path, make_record("=bad"))
    rows = sub.submissions_as_issue_rows(pd.read_csv(path))
    assert rows["review"].iloc[0] == "=bad"
    assert rows["sentiment"].iloc[0] == "positive"
    assert pd.isna(rows["error"].iloc[0])


def test_failed_llm_status_is_kept_as_error(tmp_path):
    """A submission whose analysis failed keeps its failure note."""
    path = tmp_path / "subs.csv"
    sub.append_submission(path, make_record(status="LLM unavailable"))
    rows = sub.submissions_as_issue_rows(pd.read_csv(path))
    assert rows["error"].iloc[0] == "LLM unavailable"


def test_catalog_from_processed_sample(processed_sample):
    """The product catalogue lists distinct products with department and class."""
    catalog = sub.load_product_catalog(processed_sample)
    assert catalog["Clothing ID"].is_unique
    assert {"Department Name", "Class Name"} <= set(catalog.columns)


def test_catalog_missing_file(tmp_path):
    """A missing product file raises SubmissionError."""
    with pytest.raises(SubmissionError):
        sub.load_product_catalog(tmp_path / "nope.csv")
