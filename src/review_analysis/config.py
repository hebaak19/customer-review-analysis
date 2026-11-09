"""Load project configuration and set up logging."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


NEGATIVE, NEUTRAL, POSITIVE = "negative", "neutral", "positive"
SENTIMENT_LABELS = (NEGATIVE, NEUTRAL, POSITIVE)

_REQUIRED_SECTIONS = ("paths", "columns", "labels", "cleaning")


class ConfigError(Exception):
    """The configuration file is missing or invalid."""


def load_config(path=None):
    """Load the YAML config.

    With no path, uses config/config.yaml if present, else config/config.example.yaml.
    Raises ConfigError if the file is missing, not valid YAML, or lacks a required section.
    """
    if path:
        candidates = [Path(path)]
    else:
        candidates = [CONFIG_DIR / "config.yaml", CONFIG_DIR / "config.example.yaml"]

    for candidate in candidates:
        if candidate.is_file():
            try:
                with candidate.open("r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML in {candidate}: {e}") from e
            if not isinstance(cfg, dict):
                raise ConfigError(f"{candidate} must contain a mapping of settings.")
            missing = [s for s in _REQUIRED_SECTIONS if s not in cfg]
            if missing:
                raise ConfigError(f"{candidate} is missing section(s): {missing}")
            return cfg
    raise ConfigError(f"No config file found. Tried: {[str(c) for c in candidates]}")


def resolve_path(cfg, key):
    """Return cfg['paths'][key] as an absolute path (relative paths are under the project root)."""
    try:
        raw = str(cfg["paths"][key])
    except KeyError as e:
        raise ConfigError(f"Missing path setting: {key}") from e
    # Accept Windows-style backslashes on any OS so one config works on Windows and macOS/Linux.
    p = Path(raw.replace("\\", "/"))
    return p if p.is_absolute() else PROJECT_ROOT / p


CONFIG = load_config()


TITLE_COL = CONFIG["columns"]["title"]
TEXT_COL = CONFIG["columns"]["text"]
RATING_COL = CONFIG["columns"]["rating"]
CATEGORY_COLS = list(CONFIG["columns"]["categories"])

NEGATIVE_MAX = CONFIG["labels"]["negative_max"]
POSITIVE_MIN = CONFIG["labels"]["positive_min"]

VALID_RATING_RANGE = list(CONFIG["cleaning"]["valid_ratings"])
MIN_TEXT_CHARS = CONFIG["cleaning"]["min_text_chars"]
MISSING_VALUE_PLACEHOLDER = CONFIG["cleaning"]["unknown_category"]


def setup_logging(cfg):
    """Log to the console and a rotating file. Safe to call more than once."""
    root = logging.getLogger()
    if getattr(root, "_review_logging_ready", False):
        return
    log_cfg = cfg.get("logging", {})
    root.setLevel(getattr(logging, str(log_cfg.get("level", "INFO")).upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    log_file = log_cfg.get("file")
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    root._review_logging_ready = True
