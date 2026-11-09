"""Explore the dataset and perform EDA to understand the data better."""
import pandas as pd

from review_analysis.config import CONFIG

DEFAULT_MIN_REVIEWS = CONFIG.get("issues", {}).get("min_category_reviews", 30)

CLEANED_COLUMNS = ("sentiment", "word_count")  


def _require_cleaned(df):
    """Raise a ValueError if df is not the cleaned, labelled data produced by preprocessing."""
    missing = [col for col in CLEANED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing column(s) {missing}: run the preprocessing pipeline first "
            "and pass the cleaned data (data/processed/clean_reviews.csv)."
        )


def summarize_data(df):
    """Return a summary of the DataFrame, including shape, columns, missing values, data types, and numeric summary."""
    _require_cleaned(df)
    summary = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.to_dict(),
        "numeric_summary": df.describe().to_dict()
    }
    return summary

def class_distribution(df, target_col="sentiment"):
    """Return the number of rows per value of target_col (sentiment is ordered negative, neutral, positive)."""
    _require_cleaned(df)
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in DataFrame.")
    
    distribution = df[target_col].value_counts()
    if target_col == "sentiment":  
        distribution = distribution.reindex(["negative", "neutral", "positive"], fill_value=0)
    return distribution.to_dict()

def category_sentiment_distribution(df, category_col, target_col="sentiment", min_reviews=None):
    """Return counts, total and percentages of target_col per category, dropping categories with fewer than min_reviews."""
    _require_cleaned(df)
    if category_col not in df.columns:
        raise ValueError(f"Column '{category_col}' not found in DataFrame.")
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in DataFrame.")
    
    if min_reviews is None:
        min_reviews = DEFAULT_MIN_REVIEWS

    
    counts = df.groupby(category_col)[target_col].value_counts().unstack(fill_value=0)
    if target_col == "sentiment":  
        counts = counts.reindex(columns=["negative", "neutral", "positive"], fill_value=0)
    classes = list(counts.columns)

    
    counts["total"] = counts[classes].sum(axis=1)
    counts = counts[counts["total"] >= min_reviews]

    
    percentages = counts[classes].div(counts["total"], axis=0) * 100
    percentages = percentages.round(2).add_suffix("_pct")
    result = pd.concat([counts, percentages], axis=1)

    
    sort_col = "negative_pct" if target_col == "sentiment" else "total"
    return result.sort_values(sort_col, ascending=False)