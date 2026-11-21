"""Evaluate sentiment models: metrics, confusion matrix and misclassified examples."""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from review_analysis.config import SENTIMENT_LABELS


def evaluate_predictions(y_true, predictions):
    """Return accuracy, macro-F1, per-class report and confusion matrix for predicted labels."""
    labels = list(SENTIMENT_LABELS)
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "macro_f1": float(f1_score(y_true, predictions, average="macro", labels=labels, zero_division=0)),
        "report": classification_report(y_true, predictions, labels=labels, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=labels).tolist(),
        "labels": labels,
    }


def evaluate_model(model, x_test, y_test):
    """Return accuracy, macro-F1, per-class report and confusion matrix for a model on the test set."""
    return evaluate_predictions(y_test, model.predict(x_test))


def collect_errors(model, x_test, y_test):
    """Return the misclassified test reviews with true label, prediction and confidence."""
    proba = model.predict_proba(x_test)
    predicted = model.classes_[proba.argmax(axis=1)]
    frame = pd.DataFrame(
        {
            "review": x_test.to_numpy(),
            "true": y_test.to_numpy(),
            "predicted": predicted,
            "confidence": np.round(proba.max(axis=1), 3),
        }
    )
    return frame[frame["true"] != frame["predicted"]].sort_values("confidence", ascending=False)


def top_terms_per_class(model, top_n=10):
    """Return the highest-weighted words for each class of a TF-IDF logistic regression model."""
    vocabulary = np.array(model.named_steps["tfidf"].get_feature_names_out())
    coefficients = model.named_steps["clf"].coef_
    return {
        label: vocabulary[np.argsort(coefficients[i])[::-1][:top_n]].tolist()
        for i, label in enumerate(model.classes_)
    }
