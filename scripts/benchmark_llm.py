"""Compare candidate Fuse LLMs against the TF-IDF model on one stratified sample of the test set.

Usage (from anywhere):
    python scripts/benchmark_llm.py
    python scripts/benchmark_llm.py --per-class 50
    python scripts/benchmark_llm.py --natural 600 --models deepseek-ai/DeepSeek-V4.1-Flash
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from review_analysis.config import CONFIG, ConfigError, resolve_path, setup_logging
from review_analysis.evaluation import evaluate_predictions
from review_analysis.llm import LLM_CFG, LLMError, classify_reviews, load_credentials
from review_analysis.modeling import ModelError, load_model, load_training_data, split_data

logger = logging.getLogger("benchmark_llm")


def parse_args():
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(description="Benchmark the candidate LLMs on a test-set sample.")
    parser.add_argument("--per-class", type=int, default=LLM_CFG["sample_per_class"], help="Reviews per class")
    parser.add_argument("--natural", type=int, help="Use a random sample of this size that keeps the real class mix")
    parser.add_argument("--models", nargs="+", default=LLM_CFG["models"], help="LLMs to benchmark")
    return parser.parse_args()


def main():
    """Classify a balanced test sample with every candidate model and write the comparison."""
    args = parse_args()
    setup_logging(CONFIG)
    try:
        credentials = load_credentials()
        data = load_training_data(resolve_path(CONFIG, "processed_data"))
        _, x_test, _, y_test = split_data(data)
        test = pd.DataFrame({"review": x_test, "true": y_test})
        seed = CONFIG["model"]["random_state"]
        if args.natural:
            sample = test.sample(n=args.natural, random_state=seed)
            mode = "natural"
        else:
            sample = test.groupby("true", group_keys=False).sample(n=args.per_class, random_state=seed)
            mode = "balanced"

        results = {}
        trained = load_model(resolve_path(CONFIG, "model"))
        results["tfidf_logreg"] = {**evaluate_predictions(sample["true"], trained.predict(sample["review"])), "invalid": 0, "median_seconds": 0.0}

        raw = sample.copy()
        for model_name in args.models:
            logger.info("Classifying %d reviews with %s", len(sample), model_name)
            out = classify_reviews(model_name, sample["review"], credentials)
            predictions = out["prediction"].fillna("invalid")
            raw[model_name] = predictions
            results[model_name] = {
                **evaluate_predictions(sample["true"], predictions),
                "invalid": int((predictions == "invalid").sum()),
                "median_seconds": float(out["seconds"].median()),
            }

        reports_dir = resolve_path(CONFIG, "reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / f"llm_benchmark_{mode}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        raw.to_csv(reports_dir / f"llm_benchmark_{mode}_predictions.csv", index=False)
    except (ConfigError, LLMError, ModelError) as e:
        logger.error("Benchmark failed: %s", e)
        return 1
    except OSError as e:
        logger.error("Could not write output files: %s", e)
        return 1

    print(f"\n=== {mode} sample: {len(sample)} reviews, true mix {sample['true'].value_counts().to_dict()} ===")
    for name, r in results.items():
        neutral = r["report"]["neutral"]["f1-score"]
        print(
            f"{name:36s} acc={r['accuracy']:.3f}  macro-F1={r['macro_f1']:.3f}  "
            f"neutral-F1={neutral:.3f}  invalid={r['invalid']}  median={r['median_seconds']:.1f}s"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
