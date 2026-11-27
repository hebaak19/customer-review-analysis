"""Tests for loading, validating, cleaning, labelling and exporting review data."""
import pandas as pd
import pytest

from review_analysis.preprocessing import (
    DataExportError,
    DataLoadError,
    DataValidationError,
    add_sentiment_labels,
    build_summary,
    clean_data,
    export_data,
    load_data,
    preprocess_pipeline,
    validate_data,
)


def test_load_data_reads_sample(sample_path):
    """The sample file loads and has the review columns."""
    data = load_data(sample_path)
    assert {"Review Text", "Rating"} <= set(data.columns)
    assert len(data) == 37


def test_load_data_missing_file(tmp_path):
    """A missing file raises DataLoadError."""
    with pytest.raises(DataLoadError):
        load_data(tmp_path / "nope.csv")


def test_load_data_empty_file(tmp_path):
    """An empty file raises DataLoadError."""
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(DataLoadError):
        load_data(empty)


def test_load_data_drops_unnamed_index(tmp_path):
    """An unnamed index column is removed on load."""
    path = tmp_path / "idx.csv"
    path.write_text(",Review Text,Rating\n0,hello there,5\n")
    assert "Unnamed: 0" not in load_data(path).columns


def test_validate_reports_problems(raw_sample):
    """Validation counts invalid ratings, empty text and duplicates in the sample."""
    report = validate_data(raw_sample)
    assert report["invalid_ratings"] == 1
    assert report["missing_review_text"] == 1
    assert report["duplicate_rows"] == 1


def test_validate_rejects_bad_input():
    """None, empty frames and missing columns are fatal."""
    with pytest.raises(DataValidationError):
        validate_data(None)
    with pytest.raises(DataValidationError):
        validate_data(pd.DataFrame())
    with pytest.raises(DataValidationError):
        validate_data(pd.DataFrame({"Rating": [1]}))


def test_clean_drops_unusable_rows(raw_sample):
    """Invalid rating, empty text and duplicates are dropped and counted."""
    cleaned, dropped = clean_data(raw_sample)
    assert dropped == {"invalid_rating": 1, "empty_text": 1, "duplicates": 1}
    assert len(cleaned) == len(raw_sample) - 3
    assert cleaned["Rating"].between(1, 5).all()


def test_clean_does_not_modify_input(raw_sample):
    """The input dataframe is left unchanged."""
    before = raw_sample.copy()
    clean_data(raw_sample)
    pd.testing.assert_frame_equal(raw_sample, before)


def test_clean_removes_urls_and_builds_review(raw_sample):
    """URLs are stripped and title and text are combined into the review column."""
    cleaned, _ = clean_data(raw_sample)
    assert not cleaned["review"].str.contains("http").any()
    assert cleaned["review"].iloc[0].startswith("Love it. I love this dress")


def test_clean_keeps_rows_without_title():
    """A missing title does not cause the row to be dropped."""
    data = pd.DataFrame({"Title": [None], "Review Text": ["nice dress"], "Rating": [5]})
    cleaned, _ = clean_data(data)
    assert cleaned["review"].iloc[0] == "nice dress"


def test_clean_fills_missing_categories():
    """Missing category values become Unknown."""
    data = pd.DataFrame({"Review Text": ["nice dress"], "Rating": [4], "Department Name": [None]})
    cleaned, _ = clean_data(data)
    assert cleaned["Department Name"].iloc[0] == "Unknown"


def test_clean_rejects_none():
    """clean_data rejects None."""
    with pytest.raises(DataValidationError):
        clean_data(None)


@pytest.mark.parametrize("rating,label", [(1, "negative"), (2, "negative"), (3, "neutral"), (4, "positive"), (5, "positive")])
def test_sentiment_mapping(rating, label):
    """Ratings map to sentiment at the configured thresholds."""
    df = pd.DataFrame({"Rating": [rating]})
    assert add_sentiment_labels(df)["sentiment"].iloc[0] == label


def test_sentiment_rejects_missing_rating():
    """Labelling fails when a rating is missing."""
    with pytest.raises(DataValidationError):
        add_sentiment_labels(pd.DataFrame({"Rating": [1, None]}))


def test_export_creates_folder(tmp_path):
    """Export creates missing folders and writes the CSV."""
    target = tmp_path / "a" / "b" / "out.csv"
    export_data(pd.DataFrame({"x": [1]}), target)
    assert target.is_file()


def test_export_rejects_none(tmp_path):
    """Exporting None raises DataExportError."""
    with pytest.raises(DataExportError):
        export_data(None, tmp_path / "out.csv")


def test_pipeline_end_to_end(sample_path, tmp_path):
    """The full pipeline writes a labelled file and a consistent summary."""
    out = tmp_path / "clean.csv"
    summary = preprocess_pipeline(sample_path, out)
    result = pd.read_csv(out)
    assert summary["rows_before"] == 37
    assert summary["rows_after"] == len(result) == 34
    assert set(result["sentiment"]) == {"negative", "neutral", "positive"}
    assert sum(summary["label_distribution"].values()) == len(result)
    assert "eda" in summary


def test_build_summary_counts(raw_sample):
    """The summary reports rows before and after and the label distribution."""
    cleaned, dropped = clean_data(raw_sample)
    labeled = add_sentiment_labels(cleaned)
    summary = build_summary(raw_sample, labeled, dropped)
    assert summary["rows_before"] == len(raw_sample)
    assert summary["rows_after"] == len(labeled)
