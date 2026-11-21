"""AI performance page: how well the sentiment model reads unseen reviews and how it compares with an LLM."""
import pandas as pd
import streamlit as st

from webapp import components as ui
from webapp.charts import heatmap
from webapp.theme import BLUE_RAMP
from webapp.common import LLM_MODEL, SENTIMENT_ORDER, load_report

LIMITATIONS = [
    f"{ui.strong('Labels are a proxy.')} Sentiment comes from star ratings, with 1 to 2 stars as negative, 3 as neutral and 4 to 5 as positive, not from people reading the text.",
    f"{ui.strong('Neutral is the weak class.')} Both our trained model and the language model score only about 0.3 to 0.45 on neutral, because a 3 star rating is not a distinct kind of review.",
    f"{ui.strong('Positive reviews dominate.')} About 77% of reviews are positive, so accuracy alone flatters our trained model. The macro score treats each class equally.",
    f"{ui.strong('One kind of product.')} The data covers women's clothing, so our trained model may not carry over to other products.",
    f"{ui.strong('The language model can be wrong.')} The complaint categories it finds have not been fully verified.",
]


def render():
    """Show the evaluation results of the sentiment model and its comparison with the LLM."""
    ui.page_title(
        "AI performance",
        "How well our trained sentiment model reads reviews it has never seen, and how it compares with a language model.",
    )
    metrics = load_report("model_metrics.json")
    if metrics is None:
        ui.empty_state("No results yet.", "Run scripts/train_model.py to train and score the model.")
        return

    ui.source_key(["model", "llm"])
    model = metrics["tfidf_logreg"]
    tested = sum(sum(row) for row in model["confusion_matrix"])
    ui.figures(
        [
            (f"{tested:,}", "unseen reviews used to test it", "model"),
            (f"{model['report']['negative']['recall']:.0%}", "of negative reviews found", "model"),
            (f"{model['accuracy']:.0%}", "of all reviews labelled correctly", "model"),
            (f"{model['report']['neutral']['f1-score']:.2f}", "score on neutral reviews, its weakest class", "model"),
        ]
    )

    ui.section(
        "Where it is right and where it slips",
        "Each row is the true sentiment. Each cell counts how many of those reviews the model placed in that column. Darker means a larger share of the row.",
        source="model",
    )
    matrix = pd.DataFrame(model["confusion_matrix"], index=SENTIMENT_ORDER, columns=SENTIMENT_ORDER)
    long = matrix.reset_index(names="true").melt(id_vars="true", var_name="predicted", value_name="reviews")
    long["share"] = long["reviews"] / long.groupby("true")["reviews"].transform("sum")
    label_map = {k: k.capitalize() for k in SENTIMENT_ORDER}
    long["true"] = long["true"].map(label_map)
    st.altair_chart(
        heatmap(
            long, "true", "predicted", "share", count_col="reviews", value_title="Share of the true class",
            column_order=SENTIMENT_ORDER, label_map=label_map, ramp=BLUE_RAMP,
        ),
        width="stretch",
    )

    summary = pd.DataFrame(
        [
            {"Model": "Always guess the most common class", "Accuracy": metrics["majority_baseline"]["accuracy"], "Macro score": metrics["majority_baseline"]["macro_f1"]},
            {"Model": "TF-IDF with logistic regression, used in the app", "Accuracy": model["accuracy"], "Macro score": model["macro_f1"]},
        ]
    )
    per_class = pd.DataFrame(
        {label.capitalize(): {k: model["report"][label][k] for k in ("precision", "recall", "f1-score", "support")} for label in SENTIMENT_ORDER}
    ).T.rename(columns={"precision": "Precision", "recall": "Recall", "f1-score": "F1", "support": "Reviews"})
    with st.expander("Detailed scores"):
        st.dataframe(summary.style.format({"Accuracy": "{:.3f}", "Macro score": "{:.3f}"}), hide_index=True, width="stretch")
        st.dataframe(per_class.style.format({"Precision": "{:.2f}", "Recall": "{:.2f}", "F1": "{:.2f}", "Reviews": "{:,.0f}"}), width="stretch")

    show_llm_benchmark()

    ui.section("Words it listens to", "The words that push a review toward each sentiment.", source="model")
    columns = st.columns(3, gap="large")
    for column, label in zip(columns, SENTIMENT_ORDER):
        column.markdown(f"**{label.capitalize()}**")
        column.write(", ".join(metrics["top_terms"][label]))

    ui.section("Limits to keep in mind")
    ui.notes(LIMITATIONS)


def show_llm_benchmark():
    """Show how the LLM compares with the sentiment model on the two test samples, if the reports exist."""
    rows = []
    for key, title in (("natural", "Random sample, real mix of reviews"), ("balanced", "Balanced sample, equal numbers of each class")):
        report = load_report(f"llm_benchmark_{key}.json")
        for model_name, result in (report or {}).items():
            rows.append(
                {
                    "Sample": title,
                    "Model": "TF-IDF, used in the app" if model_name == "tfidf_logreg" else model_name,
                    "Accuracy": result["accuracy"],
                    "Macro score": result["macro_f1"],
                    "Neutral": result["report"]["neutral"]["f1-score"],
                    "Negative found": result["report"]["negative"]["recall"],
                }
            )
    if not rows:
        return
    ui.section(
        "Compared with a language model",
        f"We asked {LLM_MODEL} to label the same reviews. It is about as accurate overall but finds more negative reviews. "
        "That is why the app uses it to explain complaints and keeps our trained model for sentiment.",
    )
    table = pd.DataFrame(rows)
    st.dataframe(table.style.format({c: "{:.3f}" for c in table.columns[2:]}), hide_index=True, width="stretch")
