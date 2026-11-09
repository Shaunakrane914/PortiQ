"""Answer contracts and deterministic presentation, independent of orchestration."""

import json
import math
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from portiq.config import Settings


class ToolTrace(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: float


class AgentResponse(BaseModel):
    request_id: str
    status: Literal["answer", "clarification", "unsupported", "partial", "error"]
    answer: str
    tools: list[ToolTrace]
    model: str
    model_versions: list[str]
    duration_ms: float
    model_duration_ms: float
    api_calls: int
    tokens: int
    cache: str = "disabled"
    execution_source: str = "Gemini planned analysis"
    strategy: str = "existing"
    provider_metrics: list[dict[str, Any]] = Field(default_factory=list)
    backoff_ms: float = 0
    context_portfolio: int | None = None
    error_kind: str | None = None
    error_retry_after: float | None = None
    rendering: str = "model synthesis with authoritative tool evidence"
    rendering_ms: float | None = None
    stages_ms: dict[str, float] = Field(default_factory=dict)


class AnswerAgent(Protocol):
    settings: Settings

    def answer(self, question: str) -> AgentResponse: ...


def render_response(response: AgentResponse, *, trace: bool = False, sql: bool = False) -> str:
    """Always display authoritative tool output beside the generated narrative."""
    lines = [f"[{response.status}] {response.answer}"]
    for tool in response.tools:
        if tool.error:
            lines.append(f"{tool.tool}: {tool.error}")
        if tool.result and tool.tool == "exposure_calculator":
            lines.append(f"\n{tool.result['portfolio_name']} — equity-only sector exposure")
            lines.extend(f"  {k}: {v}%" for k, v in tool.result["sectors"].items())
        if tool.result and tool.tool == "sql_query":
            lines.append("\n" + " | ".join(tool.result["columns"]))
            lines.extend(
                " | ".join("NULL" if v is None else str(v) for v in row)
                for row in tool.result["rows"]
            )
            if tool.result["truncated"]:
                lines.append("Result truncated; narrow the question for complete results.")
            if sql:
                lines.append("SQL: " + tool.result["sql"])
    if trace:
        lines.append(json.dumps(response.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return "\n".join(lines)


def _cell(value: Any, *, exact: bool = False) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, float) and not exact:
        return format(Decimal(str(value)), ",.6f").rstrip("0").rstrip(".")
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _financial(value: str, *, currency: str | None = None, percent: bool = False) -> str:
    try:
        numeric = Decimal(value)
        if not numeric.is_finite():
            return "Not available"
        text = format(numeric.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ",.2f")
    except InvalidOperation:
        return "Not available"
    return text + ("%" if percent else f" {currency}" if currency else " (currency unspecified)")


def can_render_complete(tools: list[ToolTrace]) -> bool:
    """Only complete, bounded, losslessly representable analytical evidence can finish early."""
    if not tools:
        return False
    for tool in tools:
        if tool.error or tool.result is None:
            return False
        if tool.tool == "exposure_calculator":
            continue
        if tool.tool != "sql_query":
            return False
        res = tool.result
        rows = res["rows"]
        if res.get("truncated") or not rows or len(rows) > 30:
            return False
        vals = [*res["columns"], *(v for row in rows for v in row)]
        if any(
            isinstance(v, str)
            and any(c in v for c in ("|", "\n", "\r"))
            or isinstance(v, float)
            and not math.isfinite(v)
            for v in vals
        ):
            return False
    return True


def _format_scalar_value(value: Any, *, exact: bool = False) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, int):
        return format(value, ",")
    if isinstance(value, float):
        if not math.isfinite(value):
            return "Not available"
        text = str(Decimal(str(value)))
        if "." in text:
            int_p, frac_p = text.split(".", 1)
            sign, clean = ("-" if int_p.startswith("-") else ""), int_p.lstrip("-")
            return f"{sign}{int(clean):,}.{frac_p}"
        return f"{int(text):,}"
    return str(value)


def _parse_sql_metadata(sql: str) -> dict[str, Any]:
    """Extract semantic query metadata (aliases, filters, aggregations, groupings) via AST."""
    if not sql:
        return {}
    try:
        import sqlglot
        from sqlglot import exp

        tree = sqlglot.parse_one(sql, read="sqlite")
        where, group = tree.args.get("where"), tree.args.get("group")
        w_sql = where.sql().lower() if where else ""
        return {
            "has_where": where is not None,
            "has_group": group is not None,
            "tables": [t.name.lower() for t in tree.find_all(exp.Table)],
            "is_active": any(
                k in w_sql for k in ("is_active", "status = 'active'", "status='active'", "active")
            ),
            "is_passive": any(
                k in w_sql
                for k in (
                    "status = 'passive'",
                    "status='passive'",
                    "strategy_type = 'passive'",
                    "passive",
                )
            ),
        }
    except Exception:
        return {}


def _format_label(
    column: str,
    question: str = "",
    sql_meta: dict[str, Any] | None = None,
) -> str:
    """Format an SQL column or alias into a natural human label without guessing."""
    col, q = column.strip(), question.strip().lower()
    sql_meta = sql_meta or {}
    acronyms = {"aum": "AUM", "pnl": "PnL", "id": "ID"}

    known = {
        "portfolio_count": "Total portfolios",
        "total_portfolios": "Total portfolios",
        "active_portfolios": "Active portfolios",
        "active_portfolio_count": "Active portfolios",
        "passive_portfolios": "Passive portfolios",
        "passive_portfolio_count": "Passive portfolios",
        "total_aum": "Total AUM",
        "aum": "AUM",
        "cost_basis": "Cost Basis",
        "portfolio_name": "Portfolio Name",
        "portfolio_id": "Portfolio ID",
        "security_id": "Security ID",
        "market_value": "Market Value",
        "total_market_value": "Total Market Value",
        "total_cost_basis": "Total Cost Basis",
        "current_price": "Current Price",
        "avg_current_price": "Average Current Price",
        "avg_price": "Average Price",
        "strategy_type": "Strategy Type",
        "strategy_types": "Strategy Types",
        "distinct_strategy_types": "Distinct Strategy Types",
        "distinct_asset_types": "Distinct Asset Types",
        "asset_type": "Asset Type",
        "sector_name": "Sector",
        "unrealized_pnl": "Unrealized PnL",
    }
    if col.lower() in known:
        return known[col.lower()]

    if not re.search(r"\(|\)", col):
        return " ".join(acronyms.get(w.lower(), w.capitalize()) for w in col.split("_"))

    # Unpack outer wrapper functions (ROUND, COALESCE, CAST, NULLIF)
    cleaned = col
    while m := re.match(r"(?i)^(?:round|coalesce|cast|nullif)\s*\((.*)\)$", cleaned):
        inner = m.group(1).strip()
        cleaned = (
            inner.rsplit(",", 1)[0].strip()
            if "," in inner
            else re.sub(r"(?i)\s+as\s+\w+$", "", inner).strip()
        )

    if m := re.match(r"(?i)^count\s*\((.*?)\)$", cleaned):
        inner = m.group(1).strip()
        if re.match(r"(?i)^distinct\s+", inner):
            sub = re.sub(r"(?i)^distinct\s+", "", inner).strip().replace("_", " ")
            return f"Distinct {sub} count"
        tables = sql_meta.get("tables", [])
        if sql_meta.get("has_group"):
            if "portfolios" in tables:
                return "Portfolios"
            if "securities" in tables:
                return "Securities"
            return "Count"
        entities = (
            ("portfolio", "portfolios"),
            ("fund", "portfolios"),
            ("securit", "securities"),
            ("stock", "securities"),
            ("bond", "securities"),
            ("holding", "holdings"),
            ("transaction", "transactions"),
            ("sector", "sectors"),
        )
        entity = next((v for k, v in entities if k in q or v in tables), "")
        if sql_meta.get("is_active"):
            return f"Active {entity}" if entity else "Active count"
        if sql_meta.get("is_passive"):
            return f"Passive {entity}" if entity else "Passive count"
        if qm := re.search(
            r"\b(active|passive|equity|bond|taxable|retirement|open|closed|technology|matching)\b",
            q,
        ):
            qual = qm.group(1).capitalize()
            return f"{qual} {entity}" if entity else f"{qual} count"
        if sql_meta.get("has_where"):
            return f"Matching {entity}" if entity else "Matching count"
        if (
            re.search(r"\b(total|all)\b", q)
            or re.search(r"\bhow many\b", q)
            or not sql_meta.get("has_where")
        ):
            return f"Total {entity}" if entity else "Total count"
        return entity.capitalize() if entity else "Total count"

    aggs = {
        "sum": ("Total", True),
        "avg": ("Average", False),
        "min": ("Minimum", False),
        "max": ("Maximum", False),
    }
    if m := re.match(r"(?i)^(sum|avg|min|max)\s*\((.*?)\)$", cleaned):
        func, inner = m.group(1).lower(), m.group(2).strip().replace("_", " ")
        prefix, is_title = aggs[func]
        if inner.lower() == "total aum":
            return "Total AUM"
        if not re.search(r"[*+\-/]|case\b", inner, re.I):
            return f"{prefix} {inner.title() if is_title else inner}"
        return prefix

    return col


def render_tools(
    tools: list[ToolTrace],
    *,
    max_rows: int = 30,
    exact: bool = False,
    question: str = "",
) -> str:
    sections = []
    for tool in tools:
        if tool.error:
            sections.append(tool.error)
            continue
        result = tool.result
        if not result:
            continue
        if tool.tool == "exposure_calculator":
            table_lines = ["| Sector | Exposure (%) |", "|---|---|"]
            for name, value in result["sectors"].items():
                table_lines.append(f"| {name} | {_financial(value, percent=True)} |")
            sections.append(
                f"{result['portfolio_name']} — equity-only sector exposure\n\n"
                + "\n".join(table_lines)
                + "\n\nBasis: Stock current_weight / total Stock current_weight; bonds excluded."
            )
            continue
        columns, rows = result["columns"], result["rows"]
        sql_meta = _parse_sql_metadata(
            (result or {}).get("sql") or (tool.arguments or {}).get("sql") or ""
        )
        q_context = question or (tool.arguments or {}).get("question") or ""
        if not rows:
            sections.append("No matching rows.")
        elif len(columns) == len(rows) == 1:
            label = _format_label(columns[0], q_context, sql_meta)
            sections.append(f"{label}: {_format_scalar_value(rows[0][0], exact=exact)}")
        elif len(columns) == 1 and len(rows) > 1:
            clean = _format_label(columns[0], q_context, sql_meta).lower()
            entity = (
                "portfolios"
                if "portfolio" in clean
                else "securities"
                if "securit" in clean or clean == "symbols"
                else "sectors"
                if "sector" in clean
                else clean
                if clean.endswith("s")
                else f"{clean}s"
            )
            items = [f"* {_cell(r[0], exact=exact)}" for r in rows[:max_rows]]
            sections.append(f"{len(rows)} matching {entity}:\n" + "\n".join(items))
        else:
            headers = [_format_label(c, q_context, sql_meta) for c in columns]
            table_lines = [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join("---" for _ in columns) + " |",
            ]
            table_lines.extend(
                "| " + " | ".join(_cell(v, exact=exact) for v in row) + " |"
                for row in rows[:max_rows]
            )
            sections.append("\n".join(table_lines))
        if len(rows) > max_rows or result.get("truncated"):
            sections.append(
                f"Showing up to {max_rows} rows; inspect structured results or narrow the query."
            )
    return "\n\n".join(sections) or "No successful analytical result is available."
