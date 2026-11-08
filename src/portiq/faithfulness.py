"""Deterministic result-format verification plus optional focused narrative assertions."""

import math
import re
from typing import Any

NUMBER = re.compile(
    r"(?<![\w.])(?P<number>[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)"
    r"(?:\s*(?P<scale>million|billion|thousand|[mbk])\b)?",
    re.IGNORECASE,
)
SCALES = {"million": 1e6, "billion": 1e9, "thousand": 1e3, "m": 1e6, "b": 1e9, "k": 1e3}
NO_ROWS = re.compile(
    r"\b(?:there (?:are|is) (?:no|zero)\b[^.!?\n]{0,100}\bportfolios?\b|"
    r"no (?:matching )?portfolios?\b|(?:no|zero) results?\b|none (?:were )?found\b)",
    re.IGNORECASE,
)


def _plain(text: str) -> str:
    return " ".join(text.replace("*", "").replace("`", "").split())


def _numbers(text: str) -> list[tuple[float, float]]:
    values = []
    for match in NUMBER.finditer(text):
        raw = match["number"].replace(",", "")
        scale = SCALES.get((match["scale"] or "").lower(), 1)
        number = float(raw) * scale
        tolerance = 0.5 * 10 ** -len(raw.partition(".")[2]) * scale
        if math.isfinite(number):
            values.append((number, tolerance))
    return values


def _value_present(value: Any, text: str) -> bool:
    if value is None:
        return bool(re.search(r"\b(null|not available|undefined)\b", text, re.I))
    if isinstance(value, (int, float)):
        return any(
            abs(number - value) <= (0 if isinstance(value, int) else tolerance) + 1e-6
            for number, tolerance in _numbers(text)
        )
    return bool(re.search(r"(?<!\w)" + re.escape(_plain(str(value))) + r"(?!\w)", text, re.I))


def _table_cell(value: Any, text: str) -> bool:
    if isinstance(value, (int, float)):
        return (
            len(_numbers(text)) == 1
            and not re.search(r"\bnot\b", text, re.I)
            and _value_present(value, text)
        )
    return _value_present(value, text)


def verify_answer(
    text: str,
    expected: list[dict[str, Any]],
    portfolio_names: list[str],
    sector_names: list[str] | None = None,
) -> dict[str, Any]:
    """Fail closed on incomplete scalar/list/table/exposure answers; no LLM judge.

    This verifies explicit result representations, not arbitrary English entailment.
    Multi-column Markdown tables retain column positions, preventing swapped metrics.
    """
    failures = []
    checks = 0
    clean = text.replace("*", "").replace("`", "")
    plain = _plain(text)
    empty_claim = bool(
        NO_ROWS.search(plain)
        or re.search(
            r"\bno (?:active |matching |technology |equity |stock |bond )*"
            r"(?:portfolios?|securities|holdings?|rows?|results?)\b",
            plain,
            re.I,
        )
    )
    for index, reference in enumerate(expected):
        label = f"Reference {index}"
        if "sectors" in reference:
            sectors = reference["sectors"]
            for sector in sector_names or []:
                if sector not in sectors and re.search(
                    re.escape(sector) + r"[^\d\n]{0,30}[\d.]+\s*%", clean, re.I
                ):
                    failures.append(f"{label}: unexpected sector percentage for {sector}.")
            for name in portfolio_names:
                if name != reference["portfolio_name"] and _value_present(name, plain):
                    failures.append(f"{label}: unexpected portfolio identity {name}.")
            for sector, percentage in sectors.items():
                matches = re.findall(
                    r"(?<!\w)"
                    + re.escape(sector)
                    + r"(?!\w)[^\d%+\-\n]{0,60}([+-]?\d+(?:\.\d+)?)\s*%",
                    clean,
                    re.I,
                )
                checks += 1
                if not matches or not all(_value_present(percentage, claim) for claim in matches):
                    failures.append(f"{label}: missing or incorrect percentage for {sector}.")
            if NO_ROWS.search(plain):
                failures.append(f"{label}: an empty-result claim contradicts the exposure.")
            continue
        rows = reference["rows"]
        if not rows:
            checks += 1
            if not empty_claim and not re.search(r"\bnone\b", plain, re.I):
                failures.append(f"{label}: the answer must state that no rows matched.")
            continue
        if empty_claim and rows not in [[[0]], [[None]]]:
            failures.append(f"{label}: an empty-result claim contradicts nonempty results.")
        width = len(reference["columns"])
        if len(rows) == width == 1:
            checks += 1
            value = rows[0][0]
            if value == 0 and empty_claim:
                continue
            if not _value_present(value, plain):
                failures.append(f"{label}: scalar value is missing or incorrect.")
            if re.search(r"\b(?:not|isn't|aren't)\s+[$€£]?\s*\d", plain, re.I):
                failures.append(f"{label}: negated scalar claim.")
            if isinstance(value, (int, float)) and any(
                abs(number - value) > (0 if isinstance(value, int) else tolerance) + 1e-6
                for number, tolerance in _numbers(plain)
            ):
                failures.append(f"{label}: conflicting numerical scalar claim.")
            continue
        entity = (
            "portfolios?"
            if reference["columns"] == ["portfolio_name"]
            else "securities"
            if reference["columns"][:1] == ["symbol"]
            else None
        )
        if entity:
            for count in re.findall(
                r"\b(\d+)\s+(?:(?:active|matching|technology|total)\s+)?" + entity + r"\b",
                plain,
                re.I,
            ):
                if int(count) != len(rows):
                    failures.append(f"{label}: conflicting result count {count}.")
        table_rows = []
        for line in clean.splitlines():
            if "|" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) == width:
                table_rows.append(cells)
        used: set[int] = set()
        for row in rows:
            checks += 1
            matched = next(
                (
                    i
                    for i, cells in enumerate(table_rows)
                    if i not in used
                    and all(
                        _table_cell(value, cell) for value, cell in zip(row, cells, strict=True)
                    )
                ),
                None,
            )
            if matched is not None:
                used.add(matched)
                continue
            if width == 1 and _value_present(row[0], plain):
                continue
            # Bullet lists can express string projections, e.g. company name (symbol).
            if all(isinstance(value, str) for value in row) and any(
                all(_value_present(value, _plain(line)) for value in row)
                for line in clean.splitlines()
            ):
                continue
            failures.append(f"{label}: missing or incorrect complete row {row}.")
        if reference["columns"] == ["portfolio_name"]:
            names = {row[0] for row in rows}
            for name in portfolio_names:
                if name not in names and _value_present(name, plain):
                    failures.append(f"{label}: unexpected portfolio {name}.")
    return {
        "status": "failed" if failures else "passed" if checks else "not_checked",
        "checks": checks,
        "failures": failures,
        "scope": "Explicit scalar/list/table/exposure coverage; not arbitrary prose entailment.",
    }


def check_faithfulness(
    text: str,
    expected: list[dict[str, Any]],
    rules: list[str],
    portfolio_names: list[str],
    sector_names: list[str] | None = None,
) -> dict[str, Any]:
    """Check only configured claims; absent coverage is explicitly not_checked."""
    checks: list[dict[str, Any]] = []
    plain = _plain(text)

    def add(kind: str, truth: Any, actual: Any, passed: bool) -> None:
        checks.append({"kind": kind, "expected": truth, "actual": actual, "passed": passed})

    def mentions(term: str) -> bool:
        return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", plain, re.IGNORECASE))

    for rule in rules:
        if rule in {"scalar", "portfolio_count"}:
            scalar = next(
                (
                    e["rows"][0][0]
                    for e in expected
                    if "rows" in e
                    and len(e["rows"]) == 1
                    and len(e["rows"][0]) == 1
                    and isinstance(e["rows"][0][0], (int, float))
                ),
                None,
            )
            if scalar is None:
                raise ValueError("Scalar narrative assertion requires a numeric reference cell.")
            numbers: list[float | str] = []
            matching = []
            for match in NUMBER.finditer(plain):
                raw = match["number"].replace(",", "")
                scale = SCALES.get((match["scale"] or "").lower(), 1)
                value = float(raw) * scale
                precision = len(raw.partition(".")[2])
                tolerance = 0 if rule == "portfolio_count" else 0.5 * 10**-precision * scale
                numbers.append(value if math.isfinite(value) else match["number"])
                if math.isfinite(value) and abs(value - scalar) <= tolerance + 1e-6:
                    matching.append(value)
            add("numeric_claim_present", scalar, numbers, bool(matching))
            if rule == "portfolio_count":
                claims = re.findall(
                    r"(?<!\w)([+-]?\d+)\s+(?:total\s+)?portfolios?\b", plain, re.IGNORECASE
                )
                for claim in claims:
                    add("portfolio_count_claim", scalar, int(claim), int(claim) == scalar)
        elif rule == "portfolio_names":
            names = [
                row[0]
                for e in expected
                if e.get("columns") == ["portfolio_name"]
                for row in e["rows"]
            ]
            if not names:
                raise ValueError("Portfolio list assertion requires nonempty named reference rows.")
            for name in names:
                add("required_portfolio", name, mentions(name), mentions(name))
            for name in portfolio_names:
                if name not in names and mentions(name):
                    add("unexpected_portfolio", names, name, False)
        elif rule == "exposure":
            exposures = [e for e in expected if "sectors" in e]
            if len(exposures) != 1:
                raise ValueError("Exposure prose assertion supports one portfolio at a time.")
            exposure = exposures[0]
            for name in portfolio_names:
                if mentions(name):
                    add(
                        "portfolio_identity",
                        exposure["portfolio_name"],
                        name,
                        name == exposure["portfolio_name"],
                    )
            for sector in sector_names or list(exposure["sectors"]):
                pattern = re.compile(
                    r"(?<!\w)" + re.escape(sector) + r"(?!\w)[^\d%+\-\n]{0,60}"
                    r"([+-]?\d+(?:\.\d+)?)\s*%",
                    re.IGNORECASE,
                )
                for match in pattern.finditer(text):
                    claim = match[1]
                    tolerance = 0.5 * 10 ** -len(claim.partition(".")[2])
                    percentage = exposure["sectors"].get(sector)
                    add(
                        "sector_percentage",
                        {sector: percentage},
                        float(claim),
                        percentage is not None
                        and abs(float(claim) - percentage) <= tolerance + 1e-6,
                    )
        else:
            raise ValueError(f"Unknown narrative assertion: {rule}")
    nonempty = any(
        e.get("sectors") or (e.get("rows") and e["rows"] not in [[[0]], [[None]]]) for e in expected
    )
    if rules and nonempty and NO_ROWS.search(plain):
        add("contradictory_empty_claim", "nonempty reference", "claimed no results", False)
    failed = [c for c in checks if not c["passed"]]
    return {
        "status": "failed" if failed else "passed" if checks else "not_checked",
        "rules": rules,
        "checks": checks,
        "failures": [
            f"{c['kind']}: expected {c['expected']}, actual {c['actual']}" for c in failed
        ],
        "scope": "Limited configured assertions; unchecked prose is not certified.",
    }
