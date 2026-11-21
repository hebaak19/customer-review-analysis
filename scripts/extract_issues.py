"""Extract complaint categories from the reviews with the LLM and save them for the app.

Usage (from anywhere):
    python scripts/extract_issues.py --limit 50
    python scripts/extract_issues.py

Results are appended to outputs/reports/issue_extraction.csv as they arrive, so an interrupted run resumes.
"""
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from review_analysis.config import CATEGORY_COLS, CONFIG, RATING_COL, ConfigError, resolve_path, setup_logging
from review_analysis.issue_extraction import extract_reviews, review_key
from review_analysis.llm import LLM_CFG, LLMError, load_credentials

logger = logging.getLogger("extract_issues")

CHUNK_SIZE = 200
OUTPUT_NAME = "issue_extraction.csv"


def parse_args():
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(description="Extract complaint categories from reviews with the LLM.")
    parser.add_argument("--limit", type=int, help="Process only this many randomly chosen reviews (trial run)")
    parser.add_argument("--model", default=LLM_CFG["models"][0], help="LLM to use")
    return parser.parse_args()


def main():
    """Run the extraction in chunks and append each chunk to the results file."""
    args = parse_args()
    setup_logging(CONFIG)
    try:
        credentials = load_credentials()
        data = pd.read_csv(resolve_path(CONFIG, "processed_data"))
        data["key"] = data["review"].map(review_key)
        data = data.drop_duplicates("key")
        if args.limit:
            data = data.sample(n=args.limit, random_state=CONFIG["model"]["random_state"])

        output = resolve_path(CONFIG, "reports_dir") / OUTPUT_NAME
        output.parent.mkdir(parents=True, exist_ok=True)
        done = set(pd.read_csv(output, usecols=["key"])["key"]) if output.is_file() else set()
        todo = data[~data["key"].isin(done)]
        logger.info("%d reviews to process (%d already done)", len(todo), len(done))

        keep = ["key", "review", RATING_COL, "sentiment", *CATEGORY_COLS]
        for start in range(0, len(todo), CHUNK_SIZE):
            chunk = todo.iloc[start : start + CHUNK_SIZE]
            result = extract_reviews(args.model, chunk["review"], credentials)
            rows = pd.concat([chunk[keep], result], axis=1)
            rows.to_csv(output, mode="a", header=not output.is_file(), index=False)
            logger.info("Saved %d/%d reviews", min(start + CHUNK_SIZE, len(todo)), len(todo))
    except (ConfigError, LLMError) as e:
        logger.error("Extraction failed: %s", e)
        return 1
    except OSError as e:
        logger.error("Could not read or write files: %s", e)
        return 1

    results = pd.read_csv(output)
    failed = results["error"].notna().sum()
    print(f"\n{len(results)} reviews in {output}; {failed} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
