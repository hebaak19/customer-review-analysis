"""Shared constants, cached loaders and helpers for the Streamlit pages."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from review_analysis.config import CONFIG, resolve_path
from review_analysis.issue_extraction import split_issues
from review_analysis.llm import LLM_CFG
from review_analysis.modeling import ModelError, load_model
from review_analysis.submissions import submissions_as_issue_rows

LLM_MODEL = LLM_CFG["models"][0]
SENTIMENT_ORDER = ["negative", "neutral", "positive"]
DEPARTMENT_COL = "Department Name"
CLASS_COL = "Class Name"
DATASET_SOURCE = "Dataset reviews"
CUSTOMER_SOURCE = "Customer submissions"


@st.cache_resource
def get_model():
    """Load the saved sentiment model once per server process."""
    return load_model(resolve_path(CONFIG, "model"))


@st.cache_data
def read_json(path, modified):
    """Read a JSON file, re-reading it when its modification time changes."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_data
def read_csv(path, modified):
    """Read a CSV file, re-reading it when its modification time changes."""
    return pd.read_csv(path)


def load_report(name):
    """Return a JSON report from the reports folder, or None if it does not exist."""
    path = resolve_path(CONFIG, "reports_dir") / name
    return read_json(str(path), path.stat().st_mtime) if path.is_file() else None


def get_model_or_stop():
    """Return the saved model, or show an error and stop the page if it is missing."""
    try:
        return get_model()
    except ModelError as e:
        st.error(f"{e}")
        st.stop()


def load_complaint_data():
    """Return the dataset reviews and the customer submissions in one table with a source column, or None."""
    frames = []
    issue_path = resolve_path(CONFIG, "issue_results")
    if issue_path.is_file():
        frames.append(read_csv(str(issue_path), issue_path.stat().st_mtime).assign(source=DATASET_SOURCE))
    submissions_path = resolve_path(CONFIG, "submissions")
    if submissions_path.is_file():
        saved = read_csv(str(submissions_path), submissions_path.stat().st_mtime)
        if not saved.empty:
            frames.append(submissions_as_issue_rows(saved).assign(source=CUSTOMER_SOURCE))
    return pd.concat(frames, ignore_index=True) if frames else None


def load_analysed_reviews():
    """Return the successfully analysed reviews with an issue_list column, and the sources of the failed ones."""
    data = load_complaint_data()
    if data is None:
        return None, None
    failed_sources = data.loc[data["error"].notna(), "source"]
    data = data[data["error"].isna()].copy()
    data["issue_list"] = split_issues(data["issues"])
    return (data if not data.empty else None), failed_sources
