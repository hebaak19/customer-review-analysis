"""Zero-shot review sentiment classification through the Fuse OpenAI-compatible API."""
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from dotenv import load_dotenv

from review_analysis.config import CONFIG, PROJECT_ROOT, SENTIMENT_LABELS

logger = logging.getLogger(__name__)

LLM_CFG = CONFIG["llm"]

SYSTEM_PROMPT = (
    "You classify customer reviews of women's clothing by sentiment. "
    "The label follows the star rating the customer gave: "
    "negative means 1-2 stars, neutral means 3 stars (mixed or lukewarm opinions), "
    "positive means 4-5 stars. "
    "Reply with exactly one word: negative, neutral or positive."
)

_LABEL_PATTERN = re.compile(r"\b(" + "|".join(SENTIMENT_LABELS) + r")\b", re.IGNORECASE)


class LLMError(Exception):
    """The LLM API is not configured or a request to it failed."""


def load_credentials():
    """Return the Fuse API key and base URL from the environment or the project .env file."""
    load_dotenv(PROJECT_ROOT / ".env")
    key = os.getenv("FUSE_API_KEY")
    base_url = os.getenv("FUSE_BASE_URL")
    if not key or not base_url:
        raise LLMError("FUSE_API_KEY and FUSE_BASE_URL must be set in the environment or the .env file.")
    return key, base_url.rstrip("/")


def parse_label(content):
    """Return the sentiment label found in the model reply, or None if there is not exactly one."""
    found = {m.lower() for m in _LABEL_PATTERN.findall(content or "")}
    return found.pop() if len(found) == 1 else None


def chat(model, messages, credentials, max_tokens=None):
    """Send one chat completion request with retries and return the reply text."""
    key, base_url = credentials
    payload = {
        "model": model,
        "messages": messages,
        "temperature": LLM_CFG["temperature"],
        "max_tokens": max_tokens or LLM_CFG["max_tokens"],
        "reasoning_effort": LLM_CFG["reasoning_effort"],
    }
    headers = {"Authorization": f"Bearer {key}"}
    last_error = None
    for attempt in range(LLM_CFG["max_retries"]):
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=LLM_CFG["timeout_seconds"],
            )
        except requests.RequestException as e:
            last_error = f"{type(e).__name__}"
        else:
            if response.status_code == 200:
                return response.json()["choices"][0]["message"].get("content") or ""
            last_error = f"HTTP {response.status_code}: {response.text[:200].replace(key, '***')}"
            if response.status_code not in (429, 500, 502, 503, 504):
                break
        time.sleep(2**attempt)
    raise LLMError(f"Request to {model} failed: {last_error}")


def classify_review(model, text, credentials):
    """Return the model's sentiment label for one review, or None if the reply was unusable."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Review: {text}\n\nSentiment:"},
    ]
    reply = chat(model, messages, credentials)
    return parse_label(reply)


def classify_reviews(model, texts, credentials=None):
    """Classify many reviews in parallel and return a dataframe of labels and latencies in seconds."""
    credentials = credentials or load_credentials()
    texts = pd.Series(texts)

    def run(text):
        """Classify one review and record how long the request took."""
        started = time.perf_counter()
        try:
            label = classify_review(model, text, credentials)
            error = None
        except LLMError as e:
            label, error = None, str(e)
        return {"prediction": label, "seconds": time.perf_counter() - started, "error": error}

    with ThreadPoolExecutor(max_workers=LLM_CFG["workers"]) as pool:
        rows = list(pool.map(run, texts))
    return pd.DataFrame(rows, index=texts.index)
