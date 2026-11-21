"""Page where a customer picks a product, rates and reviews it, and the review is analysed and saved."""
import streamlit as st

from review_analysis.config import CONFIG, PROJECT_ROOT, resolve_path
from review_analysis.issue_extraction import ISSUE_CATEGORIES, extract_review
from review_analysis.llm import LLMError, load_credentials
from review_analysis.modeling import class_probabilities
from review_analysis.submissions import (
    CLASS_COL,
    DEPARTMENT_COL,
    MAX_REVIEW_CHARS,
    PRODUCT_COL,
    SubmissionError,
    append_submission,
    build_record,
    load_product_catalog,
    validate_submission,
)
from webapp import components as ui
from webapp.charts import sentiment_probability_chart
from webapp.common import LLM_MODEL, get_model_or_stop

RESULT_KEY = "saved_submission"
MAX_ERROR_CHARS = 200


@st.cache_data
def get_catalog(path, modified):
    """Load the product list, re-reading it when the processed data file changes."""
    return load_product_catalog(path)


def analyse_complaints(text):
    """Return the LLM's (issues, evidence, status) for a review, with a failure status instead of raising."""
    try:
        credentials = load_credentials()
        parsed = extract_review(LLM_MODEL, text, credentials)
    except LLMError as e:
        return [], "", f"failed: {str(e)[:MAX_ERROR_CHARS]}"
    if parsed is None:
        return [], "", "failed: the LLM reply could not be read"
    return parsed[0], parsed[1], "ok"


def save_submission(model, product, rating, text):
    """Analyse the review, append it to the results file and remember the outcome for display."""
    validate_submission(product[PRODUCT_COL], rating, text)
    probabilities = class_probabilities(model, [text]).iloc[0]
    with st.spinner("Reading your review..."):
        issues, evidence, status = analyse_complaints(text)
    record = build_record(
        product[PRODUCT_COL], product[DEPARTMENT_COL], product[CLASS_COL], rating, text,
        probabilities.idxmax(), probabilities.max(), issues, evidence, status,
    )
    path = resolve_path(CONFIG, "submissions")
    append_submission(path, record)
    st.session_state[RESULT_KEY] = {"record": record, "probabilities": probabilities, "path": path}


def show_saved_submission(saved):
    """Show the outcome of a saved review, with a button to start a new one."""
    record = saved["record"]
    path = saved["path"]
    shown_path = path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path
    ui.page_title("Review submitted", "Thank you. Here is how our AI read it.")
    with st.container(border=True):
        sentiment = record["predicted_sentiment"]
        ui.html(
            f'<p class="statement">Your review reads as <strong>{sentiment}</strong>.</p>'
            f'<p class="statement-note">The model is {record["confidence"]:.0%} sure. '
            f'You rated product {record["product_id"]} in {ui.escape(record["class_name"])} {record["rating"]} out of 5.</p>'
        )
        st.altair_chart(sentiment_probability_chart(saved["probabilities"]), width="stretch")

        ui.section("What the AI found")
        if record["llm_status"] != "ok":
            st.warning("The complaint analysis is unavailable right now. Your review was still saved.")
        elif not record["llm_issues"]:
            ui.html('<p class="statement">No complaint found in this review.</p>')
        else:
            issues = record["llm_issues"].split("|")
            ui.chips([ui.issue_label(issue) for issue in issues])
            if record["llm_evidence"]:
                ui.pull_quote(record["llm_evidence"])
            with st.expander("What the categories mean"):
                for issue in issues:
                    st.write(f"**{ui.issue_label(issue)}**: {ISSUE_CATEGORIES[issue]}")
    st.caption(f"Saved to {shown_path}")
    if st.button("Write another review"):
        del st.session_state[RESULT_KEY]
        st.rerun()


def render():
    """Let the customer choose a product, rate and review it, then analyse and save the review."""
    model = get_model_or_stop()
    if RESULT_KEY in st.session_state:
        show_saved_submission(st.session_state[RESULT_KEY])
        return

    ui.page_title("Write a review", "Tell us about something you bought. Our AI reads what you write and saves it with your rating.")
    data_path = resolve_path(CONFIG, "processed_data")
    try:
        catalog = get_catalog(str(data_path), data_path.stat().st_mtime if data_path.is_file() else 0)
    except SubmissionError as e:
        st.error(str(e))
        return

    form_column, side_column = st.columns([3, 2], gap="large")
    with form_column:
        department_column, class_column, product_column = st.columns(3)
        department = department_column.selectbox("Type of clothing", sorted(catalog[DEPARTMENT_COL].unique()))
        in_department = catalog[catalog[DEPARTMENT_COL] == department]
        class_name = class_column.selectbox("Category", sorted(in_department[CLASS_COL].unique()))
        products = sorted(in_department.loc[in_department[CLASS_COL] == class_name, PRODUCT_COL])
        product_id = product_column.selectbox("Product ID", products)

        with st.form("review_form"):
            ui.html('<p class="field-label">Your rating</p>')
            rating_index = st.feedback("stars", key="rating_stars")
            text = st.text_area("Your review", height=170, max_chars=MAX_REVIEW_CHARS, placeholder="What did you like, and what could be better?")
            submitted = st.form_submit_button("Submit review")

    with side_column:
        ui.section("What happens next", flush=True)
        ui.notes(
            [
                f"Your review text is sent to an AI service ({ui.escape(LLM_MODEL)}), which finds what went wrong.",
                "A local model scores how positive or negative it reads.",
                "Both results are saved with the product and your rating.",
                "Teams read these reviews to improve fit, sizing and quality.",
            ]
        )

    if submitted:
        product = {PRODUCT_COL: product_id, DEPARTMENT_COL: department, CLASS_COL: class_name}
        rating = None if rating_index is None else rating_index + 1
        try:
            save_submission(model, product, rating, text)
        except SubmissionError as e:
            st.error(str(e))
            return
        st.rerun()
