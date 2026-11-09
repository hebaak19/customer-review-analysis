"""Visualization returns matplotlib and seaborn figures for the cleaned review dataset."""
from pathlib import Path

import seaborn as sns
from matplotlib.figure import Figure

from review_analysis.config import (
    CONFIG,
    NEGATIVE_MAX,
    POSITIVE_MIN,
    RATING_COL,
    VALID_RATING_RANGE,
    resolve_path,
)
from review_analysis.eda import category_sentiment_distribution, class_distribution

SENTIMENT_COLORS = {"negative": "#d1495b", "neutral": "#edae49", "positive": "#00798c"}


def plot_class_distribution(df, target_col="sentiment"):
    """Return a bar chart with the number of rows per value of target_col."""
    counts = class_distribution(df, target_col)  
    labels = [str(label) for label in counts]
    colors = {label: SENTIMENT_COLORS.get(label, "#6c757d") for label in labels}

    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    sns.barplot(x=labels, y=list(counts.values()), hue=labels, palette=colors, legend=False, ax=ax)
    for bars in ax.containers:  
        ax.bar_label(bars, padding=3)
    ax.set_title(f"Class distribution of {target_col}")
    ax.set_xlabel(target_col)
    ax.set_ylabel("Number of reviews")
    fig.tight_layout()
    return fig


def plot_category_sentiment_distribution(df, category_col, target_col="sentiment", min_reviews=None):
    """Return a stacked bar chart of the percentage of each class per category, worst category first."""
    table = category_sentiment_distribution(df, category_col, target_col, min_reviews)
    if table.empty:
        raise ValueError("No category has enough reviews to plot. Lower min_reviews.")

    pct_cols = [col for col in table.columns if str(col).endswith("_pct")]
    names = [str(col)[: -len("_pct")] for col in pct_cols]
    colors = [SENTIMENT_COLORS.get(name) for name in names] if target_col == "sentiment" else None

    height = max(4, 0.45 * len(table))
    fig = Figure(figsize=(10, height))
    ax = fig.subplots()
    table[pct_cols].plot(kind="barh", stacked=True, ax=ax, color=colors, width=0.8)
    ax.invert_yaxis()  
    if target_col == "sentiment":
        ax.bar_label(ax.containers[0], fmt="%.1f%%", label_type="center", color="white", fontsize=8)
    handles, _ = ax.get_legend_handles_labels()
    if ax.get_legend():
        ax.get_legend().remove()  
    ax.set_title(f"{target_col} per {category_col} (% of reviews)")
    ax.set_xlabel("% of reviews")
    ax.set_ylabel(category_col)
    ax.set_xlim(0, 100)
    fig.legend(handles, names, title=target_col, loc="lower center", ncol=len(names))
    fig.tight_layout(rect=(0, 0.9 / height, 1, 1))  
    return fig


def plot_rating_distribution(df, rating_col=RATING_COL):
    """Return a bar chart with the number of reviews per star rating, coloured by the sentiment it maps to."""
    if rating_col not in df.columns:
        raise ValueError(f"Column '{rating_col}' not found in DataFrame.")

    counts = df[rating_col].value_counts().reindex(VALID_RATING_RANGE, fill_value=0)
    labels = [str(rating) for rating in counts.index]

    def rating_color(rating):
        if rating <= NEGATIVE_MAX:
            return SENTIMENT_COLORS["negative"]
        if rating >= POSITIVE_MIN:
            return SENTIMENT_COLORS["positive"]
        return SENTIMENT_COLORS["neutral"]

    colors = {str(rating): rating_color(rating) for rating in counts.index}

    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    sns.barplot(x=labels, y=counts.tolist(), hue=labels, palette=colors, legend=False, ax=ax)
    for bars in ax.containers:  
        ax.bar_label(bars, padding=3)
    ax.set_title(f"Distribution of {rating_col}")
    ax.set_xlabel(rating_col)
    ax.set_ylabel("Number of reviews")
    fig.tight_layout()
    return fig


def save_figure(fig, name, directory=None):
    """Save the figure as <name>.png in the figures folder from the config and return the path."""
    folder = Path(directory) if directory else resolve_path(CONFIG, "figures_dir")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path
