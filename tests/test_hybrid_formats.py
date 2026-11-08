import pytest

from portiq.faithfulness import verify_answer


@pytest.mark.parametrize(
    "answer",
    [
        "## 1. Exposure\nFund A: Technology 60%; Energy 40%.\n## 2. Price\nAAPL is 185.50.",
        "| Sector | Exposure (%) |\n|---|---|\n|Technology|60|\n|Energy|40|\nAAPL is 185.50.",
        "Fund A is 60% in Technology and 40% in Energy. AAPL is 185.50.",
    ],
)
def test_hybrid_supported_formats_keep_percentages_separate_from_prices(answer):
    expected = [
        {"portfolio_name": "Fund A", "sectors": {"Technology": 60.0, "Energy": 40.0}},
        {"columns": ["current_price"], "rows": [[185.5]]},
    ]
    assert (
        verify_answer(answer, expected, ["Fund A"], ["Technology", "Energy"])["status"] == "passed"
    )
    # An exposure value must not satisfy a missing/wrong SQL scalar.
    assert (
        verify_answer(
            answer.replace("185.50", "60"), expected, ["Fund A"], ["Technology", "Energy"]
        )["status"]
        == "failed"
    )


def test_hybrid_portfolio_list_does_not_conflict_with_exposure_identity():
    expected = [
        {"portfolio_name": "Fund A", "sectors": {"Technology": 100.0}},
        {"columns": ["portfolio_name"], "rows": [["Fund B"]]},
    ]
    answer = "Fund A: Technology 100%.\nMatching portfolios: Fund B."
    assert verify_answer(answer, expected, ["Fund A", "Fund B", "Fund C"])["status"] == "passed"
    assert (
        verify_answer(answer + " Fund C.", expected, ["Fund A", "Fund B", "Fund C"])["status"]
        == "failed"
    )


def test_sql_labelled_values_do_not_consume_exposure_percentages_with_the_same_label():
    expected = [
        {"portfolio_name": "Fund A", "sectors": {"Technology": 60.0, "Energy": 40.0}},
        {"columns": ["sector_name", "avg_price"], "rows": [["Technology", 99.5]]},
    ]
    answer = "Technology: 60%; Energy: 40%.\n\nAverage prices:\n|Technology|99.5|"
    assert verify_answer(answer, expected, ["Fund A"])["status"] == "passed"
    assert verify_answer(answer.replace("99.5", "60"), expected, ["Fund A"])["status"] == "failed"
