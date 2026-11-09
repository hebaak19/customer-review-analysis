"""Create the charts for the cleaned review data and save them as PNG files.

Run scripts/run_pipeline.py first: it produces the cleaned CSV that this script reads.

Usage (from anywhere):
    python scripts/visualize_data.py
    python scripts/visualize_data.py --input data/processed/clean_reviews.csv --output-dir outputs/figures

Paths default to the values in config/config.example.yaml (or config/config.yaml if present).
"""
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from review_analysis.config import (  
    CATEGORY_COLS,
    CONFIG,
    ConfigError,
    resolve_path,
    setup_logging,
)
from review_analysis.visualization import ( 
    plot_category_sentiment_distribution,
    plot_class_distribution,
    plot_rating_distribution,
    save_figure,
)

logger = logging.getLogger("visualize_data")


def parse_args():
    parser = argparse.ArgumentParser(description="Create and save the charts for the cleaned review data.")
    parser.add_argument("--input", help="Cleaned CSV path (default: paths.processed_data in the config)")
    parser.add_argument("--output-dir", help="Folder for the PNG files (default: paths.figures_dir in the config)")
    return parser.parse_args()


def build_charts(df):
    """Return a list of (file name, function that makes the figure) for every chart to create."""
    charts = [
        ("rating_distribution", lambda: plot_rating_distribution(df)),
        ("sentiment_distribution", lambda: plot_class_distribution(df)),
    ]
    for column in CATEGORY_COLS:  
        name = "sentiment_by_" + column.lower().replace(" ", "_")
        charts.append((name, lambda column=column: plot_category_sentiment_distribution(df, column)))
    return charts


def main():
    args = parse_args()
    setup_logging(CONFIG)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)  
    try:
        input_path = Path(args.input) if args.input else resolve_path(CONFIG, "processed_data")
        output_dir = Path(args.output_dir) if args.output_dir else resolve_path(CONFIG, "figures_dir")
    except ConfigError as e:
        logger.error("Configuration problem: %s", e)
        return 1

    if not input_path.is_file():
        logger.error("Cleaned data not found: %s. Run scripts/run_pipeline.py first.", input_path)
        return 1
    try:
        df = pd.read_csv(input_path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as e:
        logger.error("Could not read %s: %s", input_path, e)
        return 1
    logger.info("Loaded %d rows from %s", len(df), input_path)

    saved, failed = [], []
    for name, make_figure in build_charts(df):
        try:
            saved.append(save_figure(make_figure(), name, output_dir))
        except (ValueError, OSError) as e:  
            logger.error("Skipped %s: %s", name, e)
            failed.append(name)

    print("\n=== Charts ===")
    for path in saved:
        print(f"Saved  : {path}")
    for name in failed:
        print(f"Failed : {name} (see the log above)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
