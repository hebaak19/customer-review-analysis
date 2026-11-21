"""Streamlit entry point: review insights for women's fashion, with sentiment, complaints and AI performance."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from review_analysis.config import ConfigError
from webapp import complaints, components, model_quality, overview, submit_review, theme


def build_pages():
    """Return the app's pages in navigation order."""
    return [
        st.Page(overview.render, title="Overview", url_path="overview", default=True),
        st.Page(submit_review.render, title="Write a review", url_path="write-a-review"),
        st.Page(complaints.render, title="Complaints", url_path="complaints"),
        st.Page(model_quality.render, title="AI performance", url_path="ai-performance"),
    ]


def main():
    """Set up the page, show the masthead and run the page chosen in it."""
    st.set_page_config(page_title="Customer review insights", layout="wide", initial_sidebar_state="collapsed")
    theme.apply_theme()
    pages = build_pages()
    current = st.navigation(pages, position="hidden")
    components.masthead(pages, current)
    try:
        current.run()
    except ConfigError as e:
        st.error(f"Configuration problem: {e}")


main()
