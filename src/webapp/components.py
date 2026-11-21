"""Small HTML building blocks for headings, figures, findings and chips, with all text escaped."""
from html import escape

import streamlit as st

from webapp.theme import INK, MULBERRY

ISSUE_LABELS = {
    "fit": "Fit",
    "size": "Sizing",
    "fabric": "Fabric",
    "quality": "Quality",
    "color": "Color",
    "price": "Price",
    "comfort": "Comfort",
    "service": "Service",
    "other": "Other",
}


def issue_label(issue):
    """Return the display name of a complaint category."""
    return ISSUE_LABELS.get(issue, str(issue).capitalize())


def html(markup):
    """Render a block of trusted HTML built from escaped parts."""
    st.markdown(markup, unsafe_allow_html=True)


def page_title(title, lede=""):
    """Show a page title with an optional one-paragraph introduction."""
    html(f'<div class="page-title" role="heading" aria-level="1">{escape(title)}</div>' + (f'<p class="lede">{escape(lede)}</p>' if lede else ""))


def section(title, note="", flush=False):
    """Show a section heading with an optional note, without top spacing when it sits beside other content."""
    html(f'<div class="section-title{" flush" if flush else ""}" role="heading" aria-level="2">{escape(title)}</div>' + (f'<p class="section-note">{escape(note)}</p>' if note else ""))


def figures(items):
    """Show a row of key figures, each given as a (value, label) pair."""
    cells = "".join(
        f'<div><div class="figure-value">{escape(str(value))}</div><div class="figure-label">{escape(label)}</div></div>'
        for value, label in items
    )
    html(f'<div class="figures">{cells}</div>')


def notes(items):
    """Show a list of findings, where each item is already-escaped HTML."""
    html('<ul class="notes">' + "".join(f"<li>{item}</li>" for item in items) + "</ul>")


def strong(text):
    """Return escaped text wrapped in bold markup, for use inside a finding."""
    return f"<strong>{escape(str(text))}</strong>"


def chips(labels):
    """Show complaint categories as outlined pills."""
    html("".join(f'<span class="chip">{escape(label)}</span>' for label in labels))


def pull_quote(text):
    """Show a customer's own words as a pull quote."""
    html(f'<div class="pull-quote">{escape(text)}</div>')


def empty_state(title, message):
    """Show a bordered empty state with what to do next."""
    html(f'<div class="empty"><strong>{escape(title)}</strong><br>{escape(message)}</div>')


def masthead(pages, current):
    """Show the page links with the current page marked, then the tape-measure rule."""
    position = pages.index(current) + 1
    html(
        f"<style>.st-key-masthead [data-testid='stColumn']:nth-child({position}) a {{ border-bottom-color: {MULBERRY}; }}"
        f".st-key-masthead [data-testid='stColumn']:nth-child({position}) a p {{ color: {INK}; }}</style>"
    )
    with st.container(key="masthead"):
        columns = st.columns([1, 1.45, 1.25, 1.55, 5], vertical_alignment="bottom")
        for column, page in zip(columns, pages):
            column.page_link(page)
    html('<div class="tape"></div>')
