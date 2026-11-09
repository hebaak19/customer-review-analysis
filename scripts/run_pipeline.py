"""Run the preprocessing pipeline.

Usage (from anywhere):
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --input data/raw/reviews.csv --output data/processed/clean_reviews.csv

Paths default to the values in config/config.example.yaml (or config/config.yaml if present).
"""
import argparse
import json
import logging
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from review_analysis.config import (  
    CONFIG,
    ConfigError,
    resolve_path,
    setup_logging,
)
from review_analysis.preprocessing import (  
    DataExportError,
    DataLoadError,
    DataValidationError,
    preprocess_pipeline,
)

logger = logging.getLogger("run_pipeline")


def parse_args():
    parser = argparse.ArgumentParser(description="Load, validate, clean, label and export the review data.")
    parser.add_argument("--input", help="Raw CSV path (default: paths.raw_data in the config)")
    parser.add_argument("--output", help="Output CSV path (default: paths.processed_data in the config)")
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(CONFIG)
    try:
        input_path = Path(args.input) if args.input else resolve_path(CONFIG, "raw_data")
        output_path = Path(args.output) if args.output else resolve_path(CONFIG, "processed_data")
        summary = preprocess_pipeline(input_path, output_path)

        reports_dir = resolve_path(CONFIG, "reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        summary_path = reports_dir / "preprocessing_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    except (ConfigError, DataLoadError, DataValidationError, DataExportError) as e:
        logger.error("Pipeline failed: %s", e)
        return 1
    except OSError as e:
        logger.error("Could not write the summary report: %s", e)
        return 1

    print("\n=== Preprocessing summary ===")
    print(f"Rows before : {summary['rows_before']:,}")
    print(f"Rows after  : {summary['rows_after']:,}")
    print(f"Dropped     : {summary['dropped_by_reason']}")
    print(f"Sentiment   : {summary['label_distribution']}")
    print(f"Cleaned data: {output_path}")
    print(f"Summary file: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
