"""Chart and table sections about complaints, shared by the overview and complaints pages."""
import pandas as pd
import streamlit as st

from review_analysis.config import CONFIG
from review_analysis.insights import group_complaint_rates, issue_shares
from review_analysis.issue_extraction import ISSUE_CATEGORIES
from webapp import components as ui
from webapp.charts import heatmap, horizontal_bars
from webapp.common import CLASS_COL, DEPARTMENT_COL
from webapp.components import ISSUE_LABELS

PREVIEW_ROWS = 200


def min_group_reviews():
    """Return the fewest reviews a department or class needs before it is shown."""
    return CONFIG["issues"]["min_category_reviews"]


def show_issue_frequency(view):
    """Show the share of reviews that mention each complaint category as bars."""
    shares = issue_shares(view)
    if shares.empty:
        ui.empty_state("No complaints in these reviews.", "Change the filters above to widen the selection.")
        return
    frame = shares.rename_axis("issue").reset_index(name="share")
    st.altair_chart(horizontal_bars(frame, "issue", "share", ".0%", label_map=ISSUE_LABELS), width="stretch")


def show_department_heatmap(view):
    """Show how often each complaint appears in each department, hiding departments with too few reviews."""
    if DEPARTMENT_COL not in view:
        return False
    minimum = min_group_reviews()
    sizes = view.groupby(DEPARTMENT_COL).size()
    keep = sizes[sizes >= min(minimum, max(sizes.max(), 1))].index
    exploded = view[view[DEPARTMENT_COL].isin(keep)].explode("issue_list").dropna(subset=["issue_list"])
    exploded = exploded[exploded["issue_list"] != ""]
    if exploded.empty:
        return False
    counts = exploded.groupby([DEPARTMENT_COL, "issue_list"]).size().unstack(fill_value=0)
    shares = counts.div(sizes[counts.index], axis=0).reset_index().melt(id_vars=DEPARTMENT_COL, var_name="issue", value_name="share")
    order = counts.sum().sort_values(ascending=False).index.tolist()
    st.altair_chart(
        heatmap(shares, DEPARTMENT_COL, "issue", "share", column_order=order, value_title="Share of department's reviews", label_map=ISSUE_LABELS),
        width="stretch",
    )
    return True


def show_top_issue_per_class(view):
    """Show the complaint rate and top complaint of each product class that has enough reviews."""
    if CLASS_COL not in view:
        return False
    rates = group_complaint_rates(view, CLASS_COL, min_group_reviews())
    rates = rates[rates["top_issue"].notna()]
    if rates.empty:
        return False
    table = pd.DataFrame(
        {
            "Product class": rates[CLASS_COL],
            "Reviews": rates["reviews"],
            "Mention a complaint": rates["rate"],
            "Top complaint": rates["top_issue"].map(lambda i: ISSUE_LABELS.get(i, i)),
            "Mentioning it": rates["top_share"],
        }
    )
    st.dataframe(
        table.style.format({"Reviews": "{:,}", "Mention a complaint": "{:.0%}", "Mentioning it": "{:.0%}"}),
        hide_index=True,
        width="stretch",
    )
    return True


def show_review_explorer(view):
    """Show a searchable table of reviews with their extracted complaints and evidence quotes."""
    left, right = st.columns(2)
    issue = left.selectbox("Complaint", ["any"] + list(ISSUE_CATEGORIES), format_func=lambda i: "Any complaint" if i == "any" else ISSUE_LABELS[i])
    query = right.text_input("Search the review text")
    shown = view
    if issue != "any":
        shown = shown[shown["issue_list"].map(lambda issues: issue in issues)]
    if query.strip():
        shown = shown[shown["review"].str.contains(query.strip(), case=False, regex=False)]
    st.caption(f"{len(shown):,} matching reviews. Showing the first {PREVIEW_ROWS}.")
    columns = [c for c in ("source", "Rating", "sentiment", DEPARTMENT_COL, "issues", "evidence", "review") if c in shown]
    table = shown[columns].head(PREVIEW_ROWS).assign(
        issues=lambda t: t["issues"].fillna("").map(lambda s: ", ".join(ISSUE_LABELS.get(i, i) for i in s.split("|") if i))
    )
    renamed = {"source": "Source", "sentiment": "Sentiment", "issues": "Complaints", "evidence": "Evidence", "review": "Review"}
    st.dataframe(table.rename(columns=renamed), hide_index=True, width="stretch")
