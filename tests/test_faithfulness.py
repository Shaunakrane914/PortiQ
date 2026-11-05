import pytest

from portiq.faithfulness import check_faithfulness


@pytest.mark.parametrize(
    "text,passed",
    [
        ("There are 13 portfolios.", True),
        ("There are 14 portfolios.", False),
        ("13 fields; there are 14 portfolios.", False),
        ("There are no portfolios. The old count was 13.", False),
    ],
)
def test_portfolio_count_claims(text: str, passed: bool) -> None:
    result = check_faithfulness(
        text, [{"columns": ["count"], "rows": [[13]]}], ["portfolio_count"], []
    )
    assert (result["status"] == "passed") == passed


@pytest.mark.parametrize("text", ["AUM is $85,000,000.", "AUM is 85 million.", "AUM is $85m."])
def test_scalar_formats(text: str) -> None:
    result = check_faithfulness(text, [{"rows": [[85000000]]}], ["scalar"], [])
    assert result["status"] == "passed"


def test_zero_count_is_not_a_false_contradiction() -> None:
    result = check_faithfulness(
        "There are no portfolios (0 portfolios).", [{"rows": [[0]]}], ["portfolio_count"], []
    )
    assert result["status"] == "passed"


def test_nonfinite_numeric_claim_cannot_produce_invalid_report_json() -> None:
    import json

    result = check_faithfulness("AUM is " + "9" * 350, [{"rows": [[85000000]]}], ["scalar"], [])
    assert result["status"] == "failed"
    json.dumps(result, allow_nan=False)


def test_named_list_rejects_missing_and_extra_identities() -> None:
    expected = [{"columns": ["portfolio_name"], "rows": [["Fund A"], ["Fund B"]]}]
    correct = check_faithfulness(
        "**Fund A** and Fund B.", expected, ["portfolio_names"], ["Fund A", "Fund B", "Fund C"]
    )
    assert correct["status"] == "passed"
    wrong = check_faithfulness(
        "Fund A and Fund C.", expected, ["portfolio_names"], ["Fund A", "Fund B", "Fund C"]
    )
    assert wrong["status"] == "failed"
    assert {c["kind"] for c in wrong["checks"] if not c["passed"]} == {
        "required_portfolio",
        "unexpected_portfolio",
    }


@pytest.mark.parametrize(
    "text,passed",
    [
        ("Fund A: Technology 61.11%.", True),
        ("Fund A: Technology 61%.", True),
        ("Fund A: Technology 62%.", False),
        ("Fund A: Technology -61.11%.", False),
        ("Fund B: Technology 61.11%.", False),
        ("Fund A: Technology 61.11%; Energy 10%.", False),
    ],
)
def test_exposure_claims(text: str, passed: bool) -> None:
    result = check_faithfulness(
        text,
        [{"portfolio_name": "Fund A", "sectors": {"Technology": 61.1111}}],
        ["exposure"],
        ["Fund A", "Fund B"],
        ["Technology", "Energy"],
    )
    assert (result["status"] == "passed") == passed


def test_unchecked_prose_and_missing_claims_are_not_certified() -> None:
    assert check_faithfulness("A confident answer.", [], [], [])["status"] == "not_checked"
    result = check_faithfulness(
        "Here is the allocation.",
        [{"portfolio_name": "Fund A", "sectors": {"Technology": 100}}],
        ["exposure"],
        ["Fund A"],
    )
    assert result["status"] == "not_checked"


@pytest.mark.parametrize(
    "rules,expected",
    [
        (["unknown"], []),
        (["scalar"], []),
        (["portfolio_names"], []),
        (["exposure"], []),
    ],
)
def test_invalid_assertion_contract_is_an_error(rules: list[str], expected: list) -> None:
    with pytest.raises(ValueError):
        check_faithfulness("Text", expected, rules, [])
