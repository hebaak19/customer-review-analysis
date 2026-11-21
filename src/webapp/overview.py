"""Overview page: the main finding about customer complaints, key figures and what stands out."""
from html import escape

import streamlit as st

from review_analysis.insights import (
    MIN_REVIEWS_FOR_FINDINGS,
    complaint_rate,
    group_complaint_rates,
    hidden_complaints,
    issue_shares,
    negative_share,
)
from webapp import components as ui
from webapp.common import CUSTOMER_SOURCE, DEPARTMENT_COL, load_analysed_reviews
from webapp.complaint_views import min_group_reviews, show_department_heatmap


def headline(data):
    """Return the headline sentence and its supporting sentence, or None when there are too few reviews."""
    shares = issue_shares(data)
    if len(data) < MIN_REVIEWS_FOR_FINDINGS or shares.empty:
        return None
    top, share = shares.index[0], float(shares.iloc[0])
    name = escape(ui.issue_label(top).lower())
    title = (
        "Customers most often raise problems outside our usual categories."
        if top == "other"
        else f"{escape(ui.issue_label(top))} is the complaint customers raise most."
    )
    lede = (
        f"The language model read {len(data):,} reviews. {share:.0%} mention {name}, and {complaint_rate(data):.0%} mention a problem of some kind, "
        "including inside four and five star reviews."
    )
    return title, lede


def findings(data):
    """Return the findings worth reading as HTML strings, skipping any the data cannot support yet."""
    items = []
    rates = group_complaint_rates(data, DEPARTMENT_COL, min_group_reviews()) if DEPARTMENT_COL in data else None
    if rates is not None and not rates.empty:
        top = rates.iloc[0]
        cause = f", most often {escape(ui.issue_label(top['top_issue']).lower())}" if top["top_issue"] else ""
        items.append(f"{ui.strong(top[DEPARTMENT_COL])} has the highest complaint rate. {top['rate']:.0%} of its reviews mention a problem{cause}.")
        if len(rates) > 1:
            low = rates.iloc[-1]
            items.append(f"{ui.strong(low[DEPARTMENT_COL])} has the lowest, at {low['rate']:.0%}.")
    hidden = hidden_complaints(data)
    if hidden and hidden["top_issue"]:
        items.append(
            f"Complaints hide inside praise. {ui.strong(f'{hidden['rate']:.0%}')} of four and five star reviews still mention a problem, "
            f"most often {escape(ui.issue_label(hidden['top_issue']).lower())}."
        )
    customer_reviews = int((data["source"] == CUSTOMER_SOURCE).sum())
    if customer_reviews:
        items.append(f"{ui.strong(f'{customer_reviews:,}')} of these reviews were written in this app.")
    return items


def render():
    """Show the overview of what customers complain about."""
    data, _ = load_analysed_reviews()
    found = headline(data) if data is not None else None
    if found is None:
        ui.html('<div class="display" role="heading" aria-level="1">Understand why customers love or return what they buy.</div>')
        ui.html('<p class="lede">This app reads customer reviews of women\'s clothing and finds what went wrong, and where.</p>')
        ui.empty_state(
            "There are not enough analysed reviews yet.",
            "Write a review, or run scripts/extract_issues.py to analyse the review dataset.",
        )
        return

    title, lede = found
    ui.html(f'<div class="display" role="heading" aria-level="1">{title}</div><p class="lede">{lede}</p>')

    rates = group_complaint_rates(data, DEPARTMENT_COL, min_group_reviews()) if DEPARTMENT_COL in data else None
    items = [
        (f"{len(data):,}", "reviews analysed", "llm"),
        (f"{complaint_rate(data):.0%}", "mention a complaint", "llm"),
        (f"{negative_share(data):.0%}", "rated one or two stars", "ratings"),
    ]
    if rates is not None and not rates.empty:
        items.append((str(rates.iloc[0][DEPARTMENT_COL]), "has the highest complaint rate", "llm"))
    ui.source_key(["llm", "ratings"])
    ui.figures(items)
    ui.html('<p class="footnote">The review count covers a random sample of the review dataset plus reviews written in this app. The language model can flag minor remarks as complaints. Our trained sentiment model is not used on this page.</p>')

    left, right = st.columns([3, 2], gap="large")
    with left:
        ui.section("Where complaints concentrate", "How often each complaint appears in each department.", source="llm")
        if not show_department_heatmap(data):
            ui.empty_state("No department pattern yet.", "More analysed reviews are needed.")
    with right:
        ui.section("What stands out", source="llm")
        points = findings(data)
        if points:
            ui.notes(points)
        else:
            ui.empty_state("Nothing to report yet.", "Findings appear once departments have enough reviews.")
