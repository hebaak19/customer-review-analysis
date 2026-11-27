"""Tests for parsing language-model replies and summarising complaints."""
import pandas as pd

from review_analysis.insights import complaint_rate, group_complaint_rates, issue_shares, negative_share
from review_analysis.issue_extraction import parse_issues, review_key, split_issues
from review_analysis.llm import parse_label


def test_parse_issues_valid_reply():
    """A valid JSON reply gives sorted known categories and the evidence."""
    issues, evidence = parse_issues('{"issues": ["size", "fit"], "evidence": "runs small"}')
    assert issues == ["fit", "size"]
    assert evidence == "runs small"


def test_parse_issues_ignores_unknown_categories_and_case():
    """Unknown categories are dropped and case is normalised."""
    issues, _ = parse_issues('{"issues": ["FIT", "weather"], "evidence": ""}')
    assert issues == ["fit"]


def test_parse_issues_finds_json_inside_text():
    """JSON surrounded by other text is still parsed."""
    assert parse_issues('Sure! {"issues": [], "evidence": ""} done') == ([], "")


def test_parse_issues_rejects_bad_replies():
    """Replies without valid JSON or an issues list return None."""
    assert parse_issues("no json here") is None
    assert parse_issues("{broken json}") is None
    assert parse_issues('{"issues": "fit"}') is None
    assert parse_issues(None) is None


def test_review_key_is_stable_and_distinct():
    """The same text gives the same key and different text gives a different key."""
    assert review_key("abc") == review_key("abc")
    assert review_key("abc") != review_key("abd")


def test_parse_label():
    """Exactly one sentiment word is accepted, anything else gives None."""
    assert parse_label("Positive") == "positive"
    assert parse_label("positive or negative") is None
    assert parse_label("unsure") is None
    assert parse_label(None) is None


def make_frame():
    """Return a small frame of extracted complaints for the summary tests."""
    return pd.DataFrame(
        {
            "issues": ["fit|size", "fit", "", "quality"],
            "sentiment": ["negative", "negative", "positive", "positive"],
            "Department Name": ["Dresses", "Dresses", "Tops", "Tops"],
        }
    )


def test_split_issues():
    """Pipe-separated issues are split into lists and blanks become empty lists."""
    assert [list(x) for x in split_issues(pd.Series(["fit|size", "", None]))] == [["fit", "size"], [], []]


def test_issue_shares_and_complaint_rate():
    """Shares and the overall complaint rate are computed over all reviews."""
    frame = make_frame()
    assert issue_shares(frame)["fit"] == 0.5
    assert complaint_rate(frame) == 0.75


def test_negative_share():
    """The negative share counts reviews labelled negative."""
    assert negative_share(make_frame()) == 0.5


def test_empty_frame_gives_zero():
    """Empty input gives zero rates instead of an error."""
    empty = pd.DataFrame({"issues": [], "sentiment": []})
    assert complaint_rate(empty) == 0.0
    assert negative_share(empty) == 0.0


def test_group_complaint_rates_respects_minimum():
    """Groups below the minimum review count are excluded."""
    assert group_complaint_rates(make_frame(), "Department Name", min_reviews=5).empty
    assert len(group_complaint_rates(make_frame(), "Department Name", min_reviews=2)) == 2
