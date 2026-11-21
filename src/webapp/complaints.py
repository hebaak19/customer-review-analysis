"""Complaints page: what customers say went wrong, with filters, charts and a searchable review table."""
import streamlit as st

from review_analysis.insights import complaint_rate
from webapp import components as ui
from webapp.common import CUSTOMER_SOURCE, DATASET_SOURCE, DEPARTMENT_COL, LLM_MODEL, SENTIMENT_ORDER, load_analysed_reviews
from webapp.complaint_views import (
    show_department_heatmap,
    show_issue_frequency,
    show_review_explorer,
    show_top_issue_per_class,
)

SMALL_SAMPLE = 500
RATING_BANDS = {"negative": "1 to 2 stars", "neutral": "3 stars", "positive": "4 to 5 stars"}


def render():
    """Show the complaint categories the LLM found in the reviews, with filters and an explorer."""
    ui.page_title(
        "Complaints",
        f"What customers say went wrong. A language model ({LLM_MODEL}) reads each review and lists the complaints, including ones hidden inside positive reviews.",
    )
    data, failed_sources = load_analysed_reviews()
    if data is None:
        ui.empty_state("No complaint data yet.", "Write a review, or run scripts/extract_issues.py to analyse the review dataset.")
        return

    ui.source_key(["llm", "ratings"])
    sources = [s for s in (DATASET_SOURCE, CUSTOMER_SOURCE) if s in set(data["source"])]
    sentiments = [s for s in SENTIMENT_ORDER if s in set(data["sentiment"])]
    departments = sorted(data[DEPARTMENT_COL].dropna().unique()) if DEPARTMENT_COL in data else []
    first, second, third = st.columns(3)
    chosen_sources = first.multiselect("Where the review is from", sources, default=sources)
    chosen_sentiments = second.multiselect("Customer's star rating", sentiments, default=sentiments, format_func=RATING_BANDS.get)
    chosen_departments = third.multiselect("Department", departments, default=departments)
    view = data[data["source"].isin(chosen_sources) & data["sentiment"].isin(chosen_sentiments)]
    if departments:
        view = view[view[DEPARTMENT_COL].isin(chosen_departments)]
    if view.empty:
        ui.empty_state("No reviews match these filters.", "Choose more sources, ratings or departments.")
        return

    ui.figures(
        [
            (f"{len(view):,}", "reviews analysed", "llm"),
            (f"{complaint_rate(view):.0%}", "mention a complaint", "llm"),
            (f"{int(failed_sources.isin(chosen_sources).sum()):,}", "could not be analysed", "llm"),
        ]
    )
    if len(view) < SMALL_SAMPLE:
        st.caption(f"Based on {len(view):,} reviews, so treat the patterns as rough.")

    ui.section("Most common complaints", "The share of reviews that mention each one. A review can mention several.", source="llm")
    show_issue_frequency(view)

    ui.section("Complaints by department", "The share of each department's reviews that mention each complaint. Departments with very few reviews are hidden.", source="llm")
    if not show_department_heatmap(view):
        ui.empty_state("No department pattern yet.", "More analysed reviews are needed.")

    ui.section("Complaints by product class", "The product classes where customers raise problems most often.", source="llm")
    if not show_top_issue_per_class(view):
        ui.empty_state("No product class has enough reviews yet.", "More analysed reviews are needed.")

    ui.section("Read the reviews", "Search the reviews behind the charts. The complaints and quotes come from the language model and can contain mistakes. The rating group comes from the customer's stars.")
    show_review_explorer(view)
