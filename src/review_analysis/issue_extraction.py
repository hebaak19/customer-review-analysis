"""Extract structured customer complaints from reviews with the Fuse LLM."""
import hashlib
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from review_analysis.config import CONFIG
from review_analysis.llm import LLM_CFG, LLMError, chat, load_credentials

logger = logging.getLogger(__name__)

ISSUE_CATEGORIES = dict(LLM_CFG["issue_categories"])
MAX_EVIDENCE_WORDS = 20

SYSTEM_PROMPT = (
    "You read customer reviews of women's clothing and list what the customer complains about.\n"
    "Use only these issue categories:\n"
    + "\n".join(f"- {name}: {description}" for name, description in ISSUE_CATEGORIES.items())
    + "\n\nRules:\n"
    "- Include a category only if the customer actually complains about it. Praise is not a complaint.\n"
    "- A positive review can still contain a complaint, for example 'love it but it runs small'.\n"
    "- If there is no complaint, return an empty list.\n"
    "- evidence is a short phrase copied from the review (at most "
    + str(MAX_EVIDENCE_WORDS)
    + " words) that shows the complaint, or an empty string.\n"
    'Reply with JSON only, in this form: {"issues": ["size", "quality"], "evidence": "runs small, zipper broke"}'
)

_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def review_key(text):
    """Return a short stable identifier for a review text, used to cache and resume results."""
    return hashlib.md5(str(text).encode("utf-8")).hexdigest()[:16]


def parse_issues(content):
    """Return (issues, evidence) parsed from the model reply, or None if the reply is not valid."""
    match = _JSON_PATTERN.search(content or "")
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    raw = payload.get("issues")
    if not isinstance(raw, list):
        return None
    issues = sorted({str(i).strip().lower() for i in raw} & set(ISSUE_CATEGORIES))
    evidence = " ".join(str(payload.get("evidence") or "").split()[:MAX_EVIDENCE_WORDS])
    return issues, evidence


def extract_review(model, text, credentials):
    """Return (issues, evidence) for one review, or None if the reply was unusable."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Review: {text}"},
    ]
    for _ in range(2):
        parsed = parse_issues(chat(model, messages, credentials, max_tokens=LLM_CFG["issue_max_tokens"]))
        if parsed is not None:
            return parsed
    return None


def extract_reviews(model, texts, credentials=None):
    """Extract complaints from many reviews in parallel and return a dataframe aligned to the input index."""
    credentials = credentials or load_credentials()
    texts = pd.Series(texts)

    def run(text):
        """Extract one review's complaints and record the outcome and latency."""
        started = time.perf_counter()
        row = {"issues": None, "evidence": None, "error": None}
        try:
            parsed = extract_review(model, text, credentials)
            if parsed is None:
                row["error"] = "unparseable reply"
            else:
                row["issues"], row["evidence"] = "|".join(parsed[0]), parsed[1]
        except LLMError as e:
            row["error"] = str(e)
        row["seconds"] = time.perf_counter() - started
        return row

    with ThreadPoolExecutor(max_workers=LLM_CFG["workers"]) as pool:
        rows = list(pool.map(run, texts))
    return pd.DataFrame(rows, index=texts.index)


def split_issues(series):
    """Turn a column of 'a|b' strings into lists of issue names, with empty strings meaning no issues."""
    return series.fillna("").map(lambda s: [i for i in s.split("|") if i])


def issue_counts_by_group(frame, group_col):
    """Return a table of how many reviews mention each issue category within each group."""
    exploded = frame.assign(issue=split_issues(frame["issues"])).explode("issue").dropna(subset=["issue"])
    return exploded.groupby([group_col, "issue"]).size().unstack(fill_value=0)
