"""Shared test fixtures and import path setup."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SAMPLE_CSV = ROOT / "tests" / "data" / "sample_reviews.csv"


@pytest.fixture(scope="session")
def sample_path():
    """Return the path of the synthetic sample reviews file."""
    return SAMPLE_CSV


@pytest.fixture()
def raw_sample():
    """Return the sample reviews as a raw dataframe."""
    return pd.read_csv(SAMPLE_CSV)


@pytest.fixture(scope="session")
def processed_sample(tmp_path_factory):
    """Run the preprocessing pipeline on the sample and return the processed CSV path."""
    from review_analysis.preprocessing import preprocess_pipeline

    out = tmp_path_factory.mktemp("processed") / "clean.csv"
    preprocess_pipeline(SAMPLE_CSV, out)
    return out
