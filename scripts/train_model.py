"""Train and evaluate the sentiment models, then save the best one.

Usage (from anywhere):
    python scripts/train_model.py
    python scripts/train_model.py --data data/processed/clean_reviews.csv
"""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from review_analysis.config import CONFIG, ConfigError, resolve_path, setup_logging
from review_analysis.evaluation import collect_errors, evaluate_model, top_terms_per_class
from review_analysis.modeling import (
    ModelError,
    build_majority_baseline,
    build_tfidf_model,
    load_training_data,
    save_model,
    split_data,
    train_model,
)

logger = logging.getLogger("train_model")


def parse_args():
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(description="Train and evaluate the sentiment classifiers.")
    parser.add_argument("--data", help="Processed CSV path (default: paths.processed_data in the config)")
    return parser.parse_args()


def main():
    """Run training and evaluation and write the metrics, errors and model files."""
    args = parse_args()
    setup_logging(CONFIG)
    try:
        data_path = Path(args.data) if args.data else resolve_path(CONFIG, "processed_data")
        data = load_training_data(data_path)
        x_train, x_test, y_train, y_test = split_data(data)

        candidates = {
            "majority_baseline": train_model(build_majority_baseline(), x_train, y_train),
            "tfidf_logreg": train_model(build_tfidf_model(), x_train, y_train),
        }
        results = {name: evaluate_model(model, x_test, y_test) for name, model in candidates.items()}
        best_name = "tfidf_logreg"
        best_model = candidates[best_name]

        reports_dir = resolve_path(CONFIG, "reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        results["best_model"] = best_name
        results["top_terms"] = top_terms_per_class(candidates["tfidf_logreg"])
        (reports_dir / "model_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        collect_errors(best_model, x_test, y_test).to_csv(reports_dir / "misclassified.csv", index=False)
        save_model(best_model, resolve_path(CONFIG, "model"))
    except (ConfigError, ModelError) as e:
        logger.error("Training failed: %s", e)
        return 1
    except OSError as e:
        logger.error("Could not write output files: %s", e)
        return 1

    print("\n=== Test-set results ===")
    for name in candidates:
        print(f"{name:20s} accuracy={results[name]['accuracy']:.3f}  macro-F1={results[name]['macro_f1']:.3f}")
    print(f"Saved model: {best_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
