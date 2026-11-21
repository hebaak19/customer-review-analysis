"""Colour tokens, typography and the global stylesheet for the Streamlit app."""
import streamlit as st

CHALK = "#F8F6F8"
PAPER = "#FFFFFF"
INK = "#2B2030"
MUTED = "#6F6475"
HAIRLINE = "#E4DCE5"
RULE = "#C9BCC9"
MULBERRY = "#7A2E5C"
ORCHID = "#F1E7F0"
SENTIMENT_COLORS = {"negative": "#C0453F", "neutral": "#A99FAD", "positive": "#00897B"}
MULBERRY_RAMP = ["#F3E6EF", "#DDB8D0", "#B97AA1", "#8F4375", "#5E2349"]

DISPLAY_FONT = "'DM Serif Display', Georgia, 'Times New Roman', serif"
BODY_FONT = "'Hanken Grotesk', 'Segoe UI', system-ui, sans-serif"

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=DM+Serif+Display:ital@0;1"
    "&family=Hanken+Grotesk:wght@400;500;600&display=swap');"
)

STYLESHEET = f"""
{FONT_IMPORT}

html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background: {CHALK};
    color: {INK};
    font-family: {BODY_FONT};
}}
.stApp p, .stApp li, .stApp label, .stApp div, .stApp span:not([data-testid="stIconMaterial"]):not([class*="material"]) {{ font-family: {BODY_FONT}; }}

[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"], [data-testid="stDecoration"], footer {{ display: none; }}

[data-testid="stMainBlockContainer"], .block-container {{
    max-width: 1120px;
    padding: 2.25rem 2rem 6rem;
}}

a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible,
[role="radio"]:focus-visible, [data-baseweb="select"]:focus-within {{
    outline: 2px solid {MULBERRY};
    outline-offset: 2px;
}}

[data-testid="stPageLink"] a, [data-testid="stPageLink-NavLink"] {{
    background: transparent;
    border-radius: 0;
    padding: 0.35rem 0;
    margin-top: 0.35rem;
    border-bottom: 2px solid transparent;
    justify-content: flex-start;
}}
[data-testid="stPageLink"] a p, [data-testid="stPageLink-NavLink"] p {{
    font-size: 0.98rem;
    font-weight: 500;
    color: {MUTED};
}}
[data-testid="stPageLink"] a:hover p, [data-testid="stPageLink-NavLink"]:hover p {{ color: {INK}; }}
[data-testid="stPageLink"] a[aria-current="page"], [data-testid="stPageLink-NavLink"][aria-current="page"] {{
    background: transparent;
    border-bottom-color: {MULBERRY};
}}
[data-testid="stPageLink"] a[aria-current="page"] p, [data-testid="stPageLink-NavLink"][aria-current="page"] p {{
    color: {INK};
}}

.tape {{
    height: 9px;
    margin: 0.9rem 0 2.75rem;
    border-bottom: 1px solid {RULE};
    background-image:
        linear-gradient(to right, {RULE} 1px, transparent 1px),
        linear-gradient(to right, {RULE} 1px, transparent 1px);
    background-size: 8px 4px, 40px 8px;
    background-repeat: repeat-x;
    background-position: left bottom;
}}

.stApp .display {{
    font-family: {DISPLAY_FONT};
    font-weight: 400;
    font-size: clamp(2.3rem, 4.8vw, 3.6rem);
    line-height: 1.04;
    letter-spacing: -0.01em;
    max-width: 24ch;
    margin: 0 0 1.25rem;
    color: {INK};
}}
.stApp .page-title {{
    font-family: {DISPLAY_FONT};
    font-weight: 400;
    font-size: clamp(2.1rem, 4vw, 3rem);
    line-height: 1.08;
    letter-spacing: -0.015em;
    margin: 0 0 0.9rem;
}}
.stApp .lede {{ font-size: 1.12rem; line-height: 1.6; color: {MUTED}; max-width: 60ch; margin: 0 0 1rem; }}

.stApp .section-title {{
    font-family: {DISPLAY_FONT};
    font-weight: 400;
    font-size: 1.65rem;
    line-height: 1.15;
    letter-spacing: -0.01em;
    margin: 3.25rem 0 0.6rem;
}}
.stApp .section-note {{ font-size: 0.96rem; line-height: 1.55; color: {MUTED}; max-width: 64ch; margin: 0 0 1.25rem; }}

.figures {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 2rem;
    border-top: 1px solid {HAIRLINE};
    padding-top: 1.4rem;
    margin: 2.25rem 0 0.5rem;
}}
.stApp .figure-value {{
    font-family: {DISPLAY_FONT};
    font-size: 2.5rem;
    font-weight: 400;
    line-height: 1;
    letter-spacing: -0.02em;
}}
.stApp .figure-label {{ font-size: 0.92rem; color: {MUTED}; margin-top: 0.5rem; line-height: 1.4; }}

.stApp .footnote {{ font-size: 0.88rem; line-height: 1.5; color: {MUTED}; max-width: 64ch; margin: 1.1rem 0 0; }}

.stApp .section-title.flush {{ margin-top: 0; }}
.stApp .field-label {{ font-size: 0.92rem; font-weight: 500; margin: 0 0 0.35rem; }}

.stApp ul.notes {{ list-style: none; padding: 0; margin: 0; border-bottom: 1px solid {HAIRLINE}; }}
.stApp ul.notes li {{ padding: 1rem 0; border-top: 1px solid {HAIRLINE}; font-size: 1rem; line-height: 1.55; }}
.stApp ul.notes strong {{ font-weight: 600; }}

.chip {{
    display: inline-block;
    padding: 0.18rem 0.75rem;
    margin: 0 0.4rem 0.4rem 0;
    border: 1px solid {MULBERRY};
    border-radius: 999px;
    color: {MULBERRY};
    font-size: 0.88rem;
    font-weight: 500;
}}
.stApp .pull-quote {{
    font-family: {DISPLAY_FONT};
    font-style: italic;
    font-size: 1.3rem;
    line-height: 1.4;
    border-left: 2px solid {MULBERRY};
    padding: 0.1rem 0 0.1rem 1.1rem;
    margin: 1rem 0 1.25rem;
    max-width: 52ch;
}}
.empty {{
    border: 1px dashed {RULE};
    border-radius: 10px;
    padding: 2rem;
    color: {MUTED};
    line-height: 1.6;
}}
.empty strong {{ color: {INK}; }}
.stApp .statement {{ font-size: 1.12rem; line-height: 1.5; margin: 0 0 0.4rem; }}
.stApp .statement-note {{ color: {MUTED}; font-size: 0.94rem; margin: 0 0 1rem; }}

[data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {{
    background: {PAPER};
    border: 1px solid {HAIRLINE};
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(43, 32, 48, 0.04);
}}
[data-testid="stForm"] {{ padding: 1.5rem 1.5rem 1.25rem; }}

[data-baseweb="select"] > div, [data-baseweb="textarea"], [data-baseweb="input"] {{
    background: {PAPER};
    border-radius: 8px;
    border-color: {HAIRLINE};
}}
[data-baseweb="tag"] {{ background: {ORCHID}; border: 1px solid {HAIRLINE}; border-radius: 999px; }}
[data-baseweb="tag"] span {{ color: {MULBERRY}; font-weight: 500; }}
[data-baseweb="tag"] svg {{ fill: {MULBERRY}; }}
[data-testid="stWidgetLabel"] p {{ font-size: 0.92rem; font-weight: 500; color: {INK}; }}

[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondaryFormSubmit"] {{
    background: {MULBERRY};
    border: 1px solid {MULBERRY};
    color: {PAPER};
    border-radius: 999px;
    padding: 0.5rem 1.6rem;
    font-weight: 500;
}}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-secondaryFormSubmit"]:hover {{
    background: #5E2349;
    border-color: #5E2349;
    color: {PAPER};
}}
[data-testid="stBaseButton-secondary"] {{
    background: transparent;
    border: 1px solid {MULBERRY};
    color: {MULBERRY};
    border-radius: 999px;
    padding: 0.5rem 1.4rem;
    font-weight: 500;
}}
[data-testid="stBaseButton-secondary"]:hover {{ background: {ORCHID}; color: {MULBERRY}; border-color: {MULBERRY}; }}

[data-testid="stAlert"] {{ border-radius: 10px; }}
[data-testid="stExpander"] {{ border: 1px solid {HAIRLINE}; border-radius: 10px; background: {PAPER}; }}
[data-testid="stDataFrame"] {{ border: 1px solid {HAIRLINE}; border-radius: 10px; overflow: hidden; }}
hr {{ border-color: {HAIRLINE}; }}

@media (max-width: 720px) {{
    [data-testid="stMainBlockContainer"], .block-container {{ padding: 1.5rem 1rem 4rem; }}
    .figure-value {{ font-size: 2rem; }}
}}
"""


def apply_theme():
    """Inject the global stylesheet into the page."""
    st.markdown(f"<style>{STYLESHEET}</style>", unsafe_allow_html=True)
