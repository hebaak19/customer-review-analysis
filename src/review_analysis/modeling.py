"""Build, train, save and load the sentiment classifiers."""
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from review_analysis.config import CONFIG, SENTIMENT_LABELS

logger = logging.getLogger(__name__)

REVIEW_COL = "review"
SENTIMENT_COL = "sentiment"
MODEL_CFG = CONFIG["model"]


class ModelError(Exception):
    """The model data, file or input is invalid."""


def load_training_data(path):
    """Read the processed CSV and return only the review text and sentiment columns."""
    path = Path(path)
    if not path.is_file():
        raise ModelError(f"Processed data not found: {path}. Run scripts/run_pipeline.py first.")
    data = pd.read_csv(path, usecols=[REVIEW_COL, SENTIMENT_COL]).dropna()
    unknown = set(data[SENTIMENT_COL]) - set(SENTIMENT_LABELS)
    if data.empty or unknown:
        raise ModelError(f"Training data is empty or has unknown labels: {sorted(unknown)}")
    return data.reset_index(drop=True)


def split_data(data):
    """Return a stratified train/test split of the data using the configured size and seed."""
    return train_test_split(
        data[REVIEW_COL],
        data[SENTIMENT_COL],
        test_size=MODEL_CFG["test_size"],
        random_state=MODEL_CFG["random_state"],
        stratify=data[SENTIMENT_COL],
    )


def _tfidf_vectorizer():
    """Return the configured TF-IDF vectorizer."""
    return TfidfVectorizer(
        max_features=MODEL_CFG["max_features"],
        ngram_range=tuple(MODEL_CFG["ngram_range"]),
        sublinear_tf=True,
        min_df=2,
    )


def _classifier():
    """Return the class-weighted logistic regression used by every model."""
    return LogisticRegression(
        C=MODEL_CFG["C"],
        class_weight=MODEL_CFG["class_weight"],
        max_iter=1000,
        random_state=MODEL_CFG["random_state"],
    )


def build_majority_baseline():
    """Return a classifier that always predicts the most frequent class."""
    return DummyClassifier(strategy="most_frequent")


def build_tfidf_model():
    """Return a TF-IDF plus class-weighted logistic regression pipeline."""
    return Pipeline([("tfidf", _tfidf_vectorizer()), ("clf", _classifier())])


def train_model(model, x_train, y_train):
    """Fit the model on the training reviews and return it."""
    model.fit(x_train, y_train)
    logger.info("Trained %s on %d reviews", type(model).__name__, len(x_train))
    return model


def save_model(model, path):
    """Save the fitted model to disk, creating the folder if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    logger.info("Model saved to %s", path)


def load_model(path):
    """Load a saved model. Raises ModelError if the file is missing or unreadable."""
    path = Path(path)
    if not path.is_file():
        raise ModelError(f"Model file not found: {path}. Run scripts/train_model.py first.")
    try:
        return joblib.load(path)
    except Exception as e:
        raise ModelError(f"Could not load model from {path}: {e}") from e


def predict_sentiment(model, texts):
    """Return a dataframe with the predicted label and confidence for each text."""
    texts = pd.Series(texts).fillna("").astype(str)
    if texts.empty:
        raise ModelError("No text to classify.")
    proba = model.predict_proba(texts)
    labels = model.classes_[proba.argmax(axis=1)]
    return pd.DataFrame({"prediction": labels, "confidence": proba.max(axis=1)}, index=texts.index)
