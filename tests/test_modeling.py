"""Tests for training, saving, predicting with and evaluating the sentiment model."""
import pandas as pd
import pytest

from review_analysis import modeling
from review_analysis.evaluation import collect_errors, evaluate_model, evaluate_predictions, top_terms_per_class
from review_analysis.modeling import ModelError


@pytest.fixture(scope="module")
def trained(processed_sample):
    """Train the TF-IDF model on the processed sample and return it with the test split."""
    data = modeling.load_training_data(processed_sample)
    x_train, x_test, y_train, y_test = modeling.split_data(data)
    model = modeling.train_model(modeling.build_tfidf_model(), x_train, y_train)
    return model, x_test, y_test


def test_load_training_data_missing_file(tmp_path):
    """A missing processed file raises ModelError."""
    with pytest.raises(ModelError):
        modeling.load_training_data(tmp_path / "nope.csv")


def test_load_training_data_unknown_labels(tmp_path):
    """Unknown sentiment labels raise ModelError."""
    path = tmp_path / "bad.csv"
    pd.DataFrame({"review": ["a b"], "sentiment": ["angry"]}).to_csv(path, index=False)
    with pytest.raises(ModelError):
        modeling.load_training_data(path)


def test_split_is_stratified_and_disjoint(processed_sample):
    """The split keeps every class in both parts and the parts do not overlap."""
    data = modeling.load_training_data(processed_sample)
    x_train, x_test, y_train, y_test = modeling.split_data(data)
    assert len(x_train) + len(x_test) == len(data)
    assert set(y_train) == set(y_test) == {"negative", "neutral", "positive"}
    assert not set(x_train.index) & set(x_test.index)


def test_predictions_are_valid_labels(trained):
    """Predictions use known labels and confidences are probabilities."""
    model, _, _ = trained
    result = modeling.predict_sentiment(model, ["I love this soft dress", "Terrible cheap fabric, returned"])
    assert set(result["prediction"]) <= {"negative", "neutral", "positive"}
    assert result["confidence"].between(0, 1).all()


def test_clear_examples_are_classified_correctly(trained):
    """Obvious positive and negative reviews get the matching label."""
    model, _, _ = trained
    result = modeling.predict_sentiment(model, ["I love it, perfect fit and soft fabric", "Awful cheap fabric, poor quality, returned"])
    assert list(result["prediction"]) == ["positive", "negative"]


def test_probabilities_sum_to_one(trained):
    """Class probabilities for each text add up to one."""
    model, _, _ = trained
    proba = modeling.class_probabilities(model, ["nice", "bad"])
    assert proba.sum(axis=1).round(6).eq(1).all()


def test_empty_input_raises(trained):
    """Classifying no text raises ModelError."""
    model, _, _ = trained
    with pytest.raises(ModelError):
        modeling.class_probabilities(model, [])


def test_missing_text_is_handled(trained):
    """A missing value is treated as empty text instead of crashing."""
    model, _, _ = trained
    assert len(modeling.predict_sentiment(model, [None])) == 1


def test_save_and_load_roundtrip(trained, tmp_path):
    """A saved model loads back and predicts the same labels."""
    model, x_test, _ = trained
    path = tmp_path / "sub" / "model.joblib"
    modeling.save_model(model, path)
    loaded = modeling.load_model(path)
    assert list(loaded.predict(x_test)) == list(model.predict(x_test))


def test_load_model_missing_and_corrupt(tmp_path):
    """Missing and corrupt model files raise ModelError."""
    with pytest.raises(ModelError):
        modeling.load_model(tmp_path / "nope.joblib")
    bad = tmp_path / "bad.joblib"
    bad.write_text("not a model")
    with pytest.raises(ModelError):
        modeling.load_model(bad)


def test_baseline_predicts_majority(processed_sample):
    """The majority baseline predicts one class for everything."""
    data = modeling.load_training_data(processed_sample)
    x_train, x_test, y_train, _ = modeling.split_data(data)
    baseline = modeling.train_model(modeling.build_majority_baseline(), x_train, y_train)
    assert len(set(baseline.predict(x_test))) == 1


def test_evaluate_predictions_perfect():
    """Perfect predictions give accuracy and macro-F1 of one."""
    labels = ["negative", "neutral", "positive"]
    result = evaluate_predictions(labels, labels)
    assert result["accuracy"] == 1.0
    assert result["macro_f1"] == 1.0
    assert result["confusion_matrix"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_evaluate_predictions_all_wrong():
    """Completely wrong predictions give accuracy of zero."""
    result = evaluate_predictions(["negative", "positive"], ["positive", "negative"])
    assert result["accuracy"] == 0.0


def test_evaluate_model_keys(trained):
    """Model evaluation returns the metrics the app displays."""
    model, x_test, y_test = trained
    result = evaluate_model(model, x_test, y_test)
    assert {"accuracy", "macro_f1", "report", "confusion_matrix", "labels"} <= set(result)
    assert 0 <= result["accuracy"] <= 1


def test_collect_errors_only_wrong_rows(trained):
    """Only misclassified reviews are returned."""
    model, x_test, y_test = trained
    errors = collect_errors(model, x_test, y_test)
    assert (errors["true"] != errors["predicted"]).all()


def test_top_terms_per_class(trained):
    """Each class gets the requested number of top terms."""
    model, _, _ = trained
    terms = top_terms_per_class(model, top_n=5)
    assert set(terms) == {"negative", "neutral", "positive"}
    assert all(len(words) == 5 for words in terms.values())
