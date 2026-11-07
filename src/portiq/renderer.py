"""Deterministic, bounded narrative from validated evidence; no question-to-answer templates."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from portiq.agent import ToolTrace


def cell(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, float):
        return format(Decimal(str(value)), ",.6f").rstrip("0").rstrip(".")
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def financial(value: str, *, currency: str | None = None, percent: bool = False) -> str:
    """Units are supplied explicitly, never inferred from the question or assumed USD."""
    try:
        numeric = Decimal(value)
        if not numeric.is_finite():
            return "Not available"
        text = format(numeric.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ",.2f")
    except InvalidOperation:
        return "Not available"
    return text + ("%" if percent else f" {currency}" if currency else " (currency unspecified)")


def render_tools(tools: list[ToolTrace], *, max_rows: int = 30) -> str:
    sections = []
    for tool in tools:
        if tool.error:
            sections.append(tool.error)
            continue
        result = tool.result
        if not result:
            continue
        if tool.tool == "exposure_calculator":
            sections.append(
                str(result["portfolio_name"])
                + " — equity-only sector exposure\n"
                + "\n".join(
                    f"{name}: {financial(value, percent=True)}"
                    for name, value in result["sectors"].items()
                )
                + "\nBasis: Stock current_weight / total Stock current_weight; bonds excluded."
            )
            continue
        columns, rows = result["columns"], result["rows"]
        if not rows:
            sections.append("No matching rows.")
        elif len(columns) == len(rows) == 1:
            value = rows[0][0]
            formatted = (
                financial(str(value))
                if value is not None
                and columns[0].lower()
                in {"current_price", "total_aum", "cost_basis", "market_value"}
                else cell(value)
            )
            sections.append(f"{columns[0]}: {formatted}")
        else:
            sections.append(
                " | ".join(cell(c) for c in columns)
                + "\n"
                + "\n".join(" | ".join(cell(v) for v in row) for row in rows[:max_rows])
            )
        if len(rows) > max_rows or result.get("truncated"):
            sections.append(
                f"Showing up to {max_rows} rows; inspect structured results or narrow the query."
            )
    return "\n\n".join(sections) or "No successful analytical result is available."
