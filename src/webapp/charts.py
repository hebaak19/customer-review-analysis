"""Altair chart builders for the Streamlit app, drawn in the app's own palette and typography."""
import altair as alt
import pandas as pd

from webapp.theme import BODY_FONT, INK, MULBERRY, MULBERRY_RAMP, MUTED, PAPER, SENTIMENT_COLORS

LIGHT_TEXT_THRESHOLD = 0.55
CHART_FONT = BODY_FONT.split(",")[0].strip("'")


def _style(chart):
    """Apply the shared fonts, colours and a transparent background to a chart."""
    return (
        chart.configure(background="rgba(0,0,0,0)", font=CHART_FONT)
        .configure_axis(domain=False, ticks=False, labelColor=INK, labelFontSize=13, titleColor=MUTED, titleFontSize=12, grid=False)
        .configure_view(stroke=None)
        .configure_legend(labelColor=INK, titleColor=MUTED, labelFontSize=12, titleFontSize=12)
    )


def horizontal_bars(frame, label_col, value_col, value_format, color=MULBERRY, color_map=None, order=None, label_map=None):
    """Return slim horizontal bars sorted by value, with the value written at the end of each bar."""
    frame = frame.copy()
    if label_map:
        frame[label_col] = frame[label_col].map(lambda v: label_map.get(v, v))
        color_map = {label_map.get(k, k): v for k, v in (color_map or {}).items()} or None
        order = [label_map.get(v, v) for v in order] if order is not None else None
    order = order if order is not None else frame.sort_values(value_col, ascending=False)[label_col].tolist()
    base = alt.Chart(frame).encode(
        y=alt.Y(f"{label_col}:N", sort=order, title=None, axis=alt.Axis(labelPadding=12)),
        x=alt.X(f"{value_col}:Q", title=None, axis=None, scale=alt.Scale(domain=[0, (float(frame[value_col].max()) or 1.0) * 1.2])),
        tooltip=[alt.Tooltip(f"{label_col}:N", title=""), alt.Tooltip(f"{value_col}:Q", title="Value", format=value_format)],
    )
    if color_map:
        scale = alt.Scale(domain=list(color_map), range=list(color_map.values()))
        bars = base.mark_bar(cornerRadiusEnd=2, size=14).encode(color=alt.Color(f"{label_col}:N", scale=scale, legend=None))
    else:
        bars = base.mark_bar(cornerRadiusEnd=2, size=14, color=color)
    labels = base.mark_text(align="left", dx=8, color=INK, fontSize=13, fontWeight=500).encode(
        text=alt.Text(f"{value_col}:Q", format=value_format)
    )
    return _style((bars + labels).properties(height=alt.Step(34)))


def heatmap(frame, row_col, column_col, value_col, count_col=None, value_title="Share", value_format=".0%", column_order=None, label_map=None, ramp=MULBERRY_RAMP, row_order=None, x_angle=0, x_orient="top"):
    """Return a single-hue heatmap with the value written in every cell."""
    frame = frame.copy()
    if label_map:
        frame[column_col] = frame[column_col].map(lambda v: label_map.get(v, v))
        frame[row_col] = frame[row_col].map(lambda v: label_map.get(v, v))
        column_order = [label_map.get(v, v) for v in column_order] if column_order is not None else None
        row_order = [label_map.get(v, v) for v in row_order] if row_order is not None else None
    value_max = float(frame[value_col].max()) or 1.0
    base = alt.Chart(frame).encode(
        x=alt.X(f"{column_col}:N", sort=column_order, title=None, axis=alt.Axis(labelAngle=x_angle, orient=x_orient, labelPadding=8, labelOverlap=False, labelFontSize=12, labelAlign="right" if x_angle < 0 else "center")),
        y=alt.Y(f"{row_col}:N", title=None, sort=row_order, axis=alt.Axis(labelPadding=10)),
        tooltip=[
            alt.Tooltip(f"{row_col}:N", title=""),
            alt.Tooltip(f"{column_col}:N", title=""),
            alt.Tooltip(f"{value_col}:Q", title=value_title, format=value_format),
        ],
    )
    cells = base.mark_rect(stroke=PAPER, strokeWidth=3).encode(
        color=alt.Color(
            f"{value_col}:Q",
            scale=alt.Scale(range=ramp, domain=[0, value_max]),
            legend=alt.Legend(title=value_title, format=value_format, orient="bottom", direction="horizontal", gradientLength=220),
        )
    )
    shown = count_col or value_col
    labels = base.mark_text(fontSize=13, fontWeight=500).encode(
        text=alt.Text(f"{shown}:Q", format="d" if count_col else value_format),
        color=alt.condition(alt.datum[value_col] > value_max * LIGHT_TEXT_THRESHOLD, alt.value(PAPER), alt.value(INK)),
    )
    return _style((cells + labels).properties(height=alt.Step(46)))


def sentiment_probability_chart(probabilities):
    """Return bars showing how likely a review is to be negative, neutral or positive."""
    frame = pd.DataFrame({"sentiment": probabilities.index, "probability": probabilities.to_numpy()})
    return horizontal_bars(
        frame, "sentiment", "probability", ".0%",
        color_map=SENTIMENT_COLORS, order=list(SENTIMENT_COLORS), label_map={k: k.capitalize() for k in SENTIMENT_COLORS},
    )

