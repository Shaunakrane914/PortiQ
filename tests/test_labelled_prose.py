import pytest

from portiq.faithfulness import verify_answer


@pytest.mark.parametrize(
    "text,passed",
    [
        ("There are 10 Active portfolios and 3 Passive portfolios.", True),
        ("Active: 10\nPassive: 3", True),
        ("Active: 3\nPassive: 10", False),
        ("Active: 10\nPassive: 3\nActive: 9", False),
        ("The values are 10 and 3.", False),
        ("Active is not 10. Passive is 3.", False),
        ("Active 10. Passive 3. There are no active portfolios.", False),
    ],
)
def test_labelled_pairs_preserve_value_association_and_reject_contradictions(text, passed):
    expected = [{"columns": ["status", "count"], "rows": [["Active", 10], ["Passive", 3]]}]
    assert (verify_answer(text, expected, [])["status"] == "passed") is passed


@pytest.mark.parametrize(
    "text,passed",
    [
        ("The minimum current price is 28.95, and maximum current price is 3380.00.", True),
        ("The minimum is 3380, and maximum is 28.95.", False),
        ("The minimum is 28.95 and maximum is 3380; minimum is actually 10.", False),
        ("Prices include 28.95 and 3380.", False),
    ],
)
def test_aggregate_prose_binds_each_metric(text, passed):
    expected = [
        {"columns": ["MIN(current_price)", "MAX(current_price)"], "rows": [[28.95, 3380.0]]}
    ]
    assert (verify_answer(text, expected, [])["status"] == "passed") is passed


def test_zero_relationship_results_are_not_an_empty_overall_result():
    expected = [
        {"columns": ["sector_name"], "rows": [["Industrials"], ["Real Estate"], ["Utilities"]]}
    ]
    answer = "The sectors with no securities are: Industrials, Real Estate, Utilities."
    assert verify_answer(answer, expected, [])["status"] == "passed"
    assert verify_answer("There are no results. " + answer, expected, [])["status"] == "failed"
