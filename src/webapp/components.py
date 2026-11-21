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

SOURCE_NAMES = {
    "llm": "Language model",
    "model": "Our trained model",
    "ratings": "Customers' star ratings",
}
BADGE_COLORS = {"llm": "violet", "model": "blue", "ratings": "orange"}


def issue_label(issue):
    """Return the display name of a complaint category."""
    return ISSUE_LABELS.get(issue, str(issue).capitalize())


def html(markup):
    """Render a block of trusted HTML built from escaped parts."""
    st.markdown(markup, unsafe_allow_html=True)


def _source_class(source):
    """Return the CSS class that colours an element by its source, or an empty string for no source."""
    return f" src-{source}" if source in SOURCE_NAMES else ""


def _source_hidden_text(source):
    """Return text read aloud by screen readers to name the source, so colour is never the only cue."""
    return f'<span class="sr-only">. Source: {escape(SOURCE_NAMES[source])}</span>' if source in SOURCE_NAMES else ""


def source_key(keys):
    """Show a one-line key of coloured badges naming where each coloured number or section comes from."""
    badges = "  ".join(f":{BADGE_COLORS[key]}-badge[{SOURCE_NAMES[key]}]" for key in keys)
    st.markdown(f"Colors show where each number comes from:  {badges}")


def page_title(title, lede=""):
    """Show a page title with an optional one-paragraph introduction."""
    html(f'<div class="page-title" role="heading" aria-level="1">{escape(title)}</div>' + (f'<p class="lede">{escape(lede)}</p>' if lede else ""))


def section(title, note="", flush=False, source=None):
    """Show a section heading, with a coloured accent bar when its numbers come from a known source."""
    heading = (
        f'<div class="section-title{_source_class(source)}{" flush" if flush else ""}" role="heading" aria-level="2">'
        f"{escape(title)}{_source_hidden_text(source)}</div>"
    )
    html(heading + (f'<p class="section-note">{escape(note)}</p>' if note else ""))


def figures(items):
    """Show a row of key figures given as (value, label, source), each topped by a rule in its source colour."""
    cells = "".join(
        f'<div class="figure{_source_class(source)}"><div class="figure-value">{escape(str(value))}</div>'
        f'<div class="figure-label">{escape(label)}{_source_hidden_text(source)}</div></div>'
        for value, label, source in items
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
    """Show the page links in a row that wraps on small screens, with the current page marked."""
    index = pages.index(current)
    html(
        f"<style>.st-key-nav_{index} a {{ border-bottom-color: {MULBERRY}; }}"
        f".st-key-nav_{index} a p {{ color: {INK}; }}</style>"
    )
    with st.container(key="masthead", horizontal=True, gap="large"):
        for position, page in enumerate(pages):
            with st.container(key=f"nav_{position}", width="content"):
                st.page_link(page)
    html('<div class="tape"></div>')
