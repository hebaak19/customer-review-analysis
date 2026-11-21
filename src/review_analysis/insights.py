"""Summarise LLM-extracted complaints into the figures and findings shown on the overview."""
import pandas as pd

from review_analysis.config import NEGATIVE, POSITIVE
from review_analysis.issue_extraction import split_issues

MIN_REVIEWS_FOR_FINDINGS = 30


def _with_issue_lists(frame):
    """Return the frame with an issue_list column of complaint names, adding it when missing."""
    return frame if "issue_list" in frame else frame.assign(issue_list=split_issues(frame["issues"]))


def issue_shares(frame):
    """Return the share of reviews that mention each complaint category, largest first."""
    frame = _with_issue_lists(frame)
    mentions = frame["issue_list"].explode().dropna()
    mentions = mentions[mentions != ""]
    return mentions.value_counts().div(len(frame)) if len(frame) else pd.Series(dtype=float)


def complaint_rate(frame):
    """Return the share of reviews that mention at least one complaint."""
    frame = _with_issue_lists(frame)
    return float((frame["issue_list"].map(len) > 0).mean()) if len(frame) else 0.0


def negative_share(frame):
    """Return the share of reviews whose star rating makes them negative."""
    return float((frame["sentiment"] == NEGATIVE).mean()) if len(frame) else 0.0


def group_complaint_rates(frame, group_col, min_reviews=MIN_REVIEWS_FOR_FINDINGS):
    """Return the complaint rate and top complaint for each group with enough reviews, highest rate first."""
    frame = _with_issue_lists(frame)
    rows = []
    for name, group in frame.groupby(group_col):
        if len(group) < min_reviews:
            continue
        shares = issue_shares(group)
        rows.append(
            {
                group_col: name,
                "reviews": len(group),
                "rate": complaint_rate(group),
                "top_issue": shares.index[0] if len(shares) else None,
                "top_share": float(shares.iloc[0]) if len(shares) else 0.0,
            }
        )
    columns = [group_col, "reviews", "rate", "top_issue", "top_share"]
    return pd.DataFrame(rows, columns=columns).sort_values("rate", ascending=False).reset_index(drop=True)


def hidden_complaints(frame, min_reviews=MIN_REVIEWS_FOR_FINDINGS):
    """Return the share of positive reviews that still mention a complaint and the most common one, or None."""
    positive = _with_issue_lists(frame[frame["sentiment"] == POSITIVE])
    if len(positive) < min_reviews:
        return None
    shares = issue_shares(positive)
    return {"rate": complaint_rate(positive), "top_issue": shares.index[0] if len(shares) else None, "reviews": len(positive)}
