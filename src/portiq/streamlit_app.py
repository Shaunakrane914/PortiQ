"""Optional Streamlit workspace sharing the dashboard's design and analytical services."""

import csv
import io
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from portiq.agent import AgentResponse
from portiq.analytics import Snapshot
from portiq.config import Settings
from portiq.database import initialize
from portiq.errors import PortiqError
from portiq.service import AnalysisService

PAGES = {
    "AI Analyst": "Ask about your portfolios. Get answers with evidence.",
    "Overview": "The recorded portfolio universe, at a glance.",
    "Portfolio Explorer": "Explore holdings, exposure and recorded observations.",
    "Reconciliation": "Two valid lenses. Make their differences visible.",
}
GOLD = "#B69C6A"


@st.cache_resource  # type: ignore[untyped-decorator]
def analysis_service() -> AnalysisService:
    settings = Settings.from_env()
    if not settings.database.exists():
        initialize(settings.source, settings.database)
    return AnalysisService(settings)


def heading(title: str, kicker: str = "RECORDED DATA") -> None:
    st.html(
        f'<div class="card-head"><h2>{escape(title)}</h2>'
        f'<span class="kicker">{escape(kicker)}</span></div>'
    )


def metric(label: str, value: Any, description: str) -> None:
    st.html(
        f'<div class="metric"><div class="label">{escape(label)}</div>'
        f'<div class="value">{escape(str(value))}</div>'
        f'<div class="description">{escape(description)}</div></div>'
    )


def exposure_chart(snapshot: Snapshot) -> None:
    if snapshot.exposure is None:
        st.info("Equity exposure is undefined: no positive equity denominator.")
        return
    sectors = snapshot.exposure.sectors
    st.bar_chart(
        {"Sector": list(sectors), "Exposure (%)": [float(v) for v in sectors.values()]},
        x="Sector",
        y="Exposure (%)",
        horizontal=True,
        color=GOLD,
    )
    st.caption("Denominator: total recorded Stock weight. Bonds excluded.")


def message(item: dict[str, Any]) -> None:
    response = item.get("response")
    label = "YOU" if item["role"] == "user" else "PORTIQ / SOURCE-BACKED ANSWER"
    st.html(
        f'<div class="message {"user" if item["role"] == "user" else ""}">'
        f'<div class="kicker">{label}</div><pre>{escape(item["text"])}</pre></div>'
    )
    if response is None:
        return
    result = AgentResponse.model_validate(response)
    service_ms = sum(item.get("service_ms", 0) for item in result.provider_metrics)
    pacing_ms = sum(item.get("pacing_ms", 0) for item in result.provider_metrics)
    st.caption(
        f"{result.status} · {result.api_calls} SDK calls · {result.tokens:,} reported tokens · "
        f"{result.duration_ms / 1000:.2f}s total · {service_ms / 1000:.2f}s service · "
        f"{pacing_ms / 1000:.2f}s pacing · cache {result.cache} · {result.model}"
    )
    for tool in result.tools:
        with st.expander(
            tool.tool + " · " + ("needs clarification" if tool.error else "validated result")
        ):
            if tool.error:
                st.write("This analysis step could not be completed.")
            elif tool.result:
                data = tool.result
                if data.get("sql"):
                    st.code(data["sql"], language="sql")
                if "rows" in data:
                    columns = data["columns"]
                    st.dataframe(
                        {
                            (f"{i + 1}. {name}" if columns.count(name) > 1 else name): [
                                row[i] for row in data["rows"]
                            ]
                            for i, name in enumerate(columns)
                        },
                        hide_index=True,
                        width="stretch",
                    )
                if "sectors" in data:
                    st.dataframe(
                        {
                            "Sector": list(data["sectors"]),
                            "Exposure (%)": list(data["sectors"].values()),
                        },
                        hide_index=True,
                        width="stretch",
                    )


def analyst(service: AnalysisService, selected: int | None) -> None:
    with st.container(border=True, key="card_analyst"):
        heading("A conversation with evidence", "PORTFOLIO QUESTIONS")
        st.info(
            "Ask about recorded portfolio data. AI questions and relevant tool results are sent "
            "to Google Gemini; avoid entering personal or confidential information."
        )
        messages: list[dict[str, Any]] = st.session_state.setdefault("messages", [])
        if not messages:
            st.html(
                '<div class="portiq-empty-chat">Your research starts with a question.<br>'
                "<small>Explore holdings, compare recorded figures, "
                "or calculate sector exposure.</small></div>"
            )
        for item in messages:
            message(item)
        columns = st.columns(3)
        suggestions = ["Count all portfolios", "Show holdings", "Calculate sector exposure"]
        for column, label in zip(columns, suggestions, strict=True):
            if column.button(label, width="stretch"):
                reference = str(selected) if selected is not None else "the selected portfolio"
                st.session_state["gui_question"] = (
                    label if label == "Count all portfolios" else f"{label} for {reference}"
                )

        def change_answer_mode() -> None:
            if st.session_state.get("gui_smarter"):
                st.session_state["gui_local"] = False
                st.session_state["gui_cached"] = False

        smarter = st.checkbox(
            "Smarter answer (2 SDK)",
            value=False,
            key="gui_smarter",
            on_change=change_answer_mode,
            help="Gemini reviews results and adds explanation. Usually 2 calls; analysis, "
            "repairs or retries can add more. Uses live Gemini with local fast path and cache off.",
        )
        with st.form("analyst_question", clear_on_submit=True):
            question = st.text_area(
                "Ask PortiQ",
                key="gui_question",
                label_visibility="collapsed",
                max_chars=3500,
                placeholder="Ask about holdings, exposure or recorded observations…",
            )
            controls = st.columns(3)
            local = controls[0].checkbox(
                "Local fast path", value=False, key="gui_local", disabled=smarter
            )
            cached = controls[1].checkbox(
                "Exact cache", value=False, key="gui_cached", disabled=smarter
            )
            context = controls[2].checkbox("Conversation context", value=False)
            left, right = st.columns([3, 1])
            reset = left.form_submit_button("New conversation", key="gui_reset")
            submitted = right.form_submit_button(
                "Analyze →", type="primary", width="stretch", key="gui_analyze"
            )
        if reset:
            st.session_state.pop("conversation_id", None)
            st.session_state["messages"] = []
            st.rerun()
        if submitted and not question.strip():
            st.info("Type a question before analyzing.")
        if submitted and question.strip():
            messages.append({"role": "user", "text": question})
            with st.spinner("Analyzing recorded data…"):
                try:
                    result, session = service.ask(
                        question,
                        selected=selected,
                        session_id=st.session_state.get("conversation_id"),
                        conversation=context,
                        local=local,
                        cached=cached,
                        smarter=smarter,
                    )
                    st.session_state["conversation_id"] = session
                    if context:
                        st.session_state["gui_next_portfolio"] = result.context_portfolio
                    text = (
                        "Analysis is temporarily unavailable. Please try again later."
                        if result.status == "error"
                        else result.answer
                    )
                    messages.append(
                        {
                            "role": "assistant",
                            "text": text,
                            "response": result.model_dump(mode="json"),
                        }
                    )
                except PortiqError:
                    messages.append(
                        {
                            "role": "assistant",
                            "text": "Analysis is temporarily unavailable. Please try again later.",
                        }
                    )
            st.session_state["messages"] = messages[-32:]
            st.rerun()


def overview(service: AnalysisService, selected: int | None) -> None:
    data = service.portfolios.overview()
    for column, label, field, note in zip(
        st.columns(3),
        ["Portfolio universe", "Active mandates", "Listed holdings"],
        ["portfolio_count", "active_count", "holding_count"],
        [
            "Distinct recorded portfolios",
            "Recorded status = Active",
            "Positions in the supplied universe",
        ],
        strict=True,
    ):
        with column:
            metric(label, data[field], note)
    left, right = st.columns(2)
    with left, st.container(border=True, key="card_overview_exposure"):
        heading("Equity sector allocation", "SELECTED PORTFOLIO")
        if selected is not None:
            exposure_chart(service.portfolios.snapshot(selected))
        else:
            st.write("Choose a portfolio to see its equity sector allocation.")
    with right, st.container(border=True, key="card_overview_scope"):
        heading("Research scope", "CALCULATION NOTES")
        st.write(
            "Historical, sparse observations. "
            "No price, return or risk value is represented as live."
        )
        st.caption(
            "AUM currency and valuation date are unspecified. "
            "No cross-portfolio aggregate is inferred."
        )
    with st.container(border=True, key="card_universe"):
        heading("The portfolio universe", "RECORDED MANDATES")
        st.dataframe(data["portfolios"], hide_index=True, width="stretch")


def explorer(snapshot: Snapshot) -> None:
    portfolio = snapshot.portfolio
    for column, label, value, note in zip(
        st.columns(4),
        ["Status", "Recorded AUM", "Holdings", "Target risk"],
        [
            portfolio["status"],
            f"{portfolio['total_aum']:,.0f}"
            if isinstance(portfolio["total_aum"], (int, float))
            else "Not recorded",
            len(snapshot.holdings),
            portfolio["target_risk_level"],
        ],
        [
            portfolio["strategy_type"],
            "Currency / valuation date unspecified",
            "Listed positions",
            portfolio.get("benchmark_index") or "Recorded classification",
        ],
        strict=True,
    ):
        with column:
            metric(label, value, note)
    left, right = st.columns(2)
    with left, st.container(border=True, key="card_explorer_exposure"):
        heading("Equity sector exposure", "EQUITY DENOMINATOR")
        exposure_chart(snapshot)
    with right, st.container(border=True, key="card_composition"):
        heading("Recorded asset composition", "WHOLE-PORTFOLIO WEIGHTS")
        st.dataframe(
            {
                "Asset type": list(snapshot.composition_percent),
                "Recorded weight (%)": list(snapshot.composition_percent.values()),
            },
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Denominator: recorded whole-portfolio weight (1.0). No cash allocation is inferred."
        )
    for title, records in [
        ("Holdings", [h.model_dump() for h in snapshot.holdings]),
        ("Recorded performance", snapshot.performance),
        ("Recorded risk", snapshot.risk),
        ("Recorded prices", snapshot.prices),
    ]:
        with st.container(border=True, key="card_" + title.replace(" ", "_")):
            heading(title, "SOURCE-BACKED OBSERVATIONS")
            st.dataframe(records, hide_index=True, width="stretch")


def reconciliation(snapshot: Snapshot) -> None:
    data = snapshot.reconciliation
    with st.container(border=True, key="card_reconciliation"):
        heading("Recorded vs reconstructed allocation", "EXPLICIT WEIGHT BASES")
        st.write(data.methodology)
        rows = [row.model_dump() for row in data.rows]
        st.dataframe(rows, hide_index=True, width="stretch")
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        key: "'" + str(value)
                        if isinstance(value, str)
                        and value.lstrip().startswith(("=", "+", "-", "@"))
                        else value
                        for key, value in row.items()
                    }
                )
        st.download_button(
            "Export reconciliation CSV",
            output.getvalue(),
            file_name="reconciliation.csv",
            mime="text/csv",
        )
        for warning in data.warnings:
            st.caption(warning.message)


def main() -> None:
    st.set_page_config(page_title="PortiQ · Portfolio Intelligence", page_icon="P", layout="wide")
    assets = Path(__file__).parent / "web"
    st.html(
        "<style>"
        + (assets / "styles.css").read_text(encoding="utf-8")
        + (assets / "streamlit.css").read_text(encoding="utf-8")
        + "</style>"
    )
    with st.sidebar:
        st.html(
            '<div class="brand"><span class="mark">P<span>iQ</span></span>'
            "<span>PortiQ<small>PORTFOLIO INTELLIGENCE</small></span></div>"
            '<div class="rail-label">RESEARCH WORKSPACE</div>'
        )
        page = st.radio(
            "Workspace",
            list(PAGES),
            label_visibility="collapsed",
            format_func=lambda label: f"{list(PAGES).index(label) + 1:02d}   {label}",
        )
        st.html(
            '<div class="rail-footer"><span class="dot"></span>Recorded demonstration data'
            "<p>Portfolio research,<br>with a clear calculation basis.</p>"
            "<small>Local analytics · Traceable answers</small></div>"
        )
    st.html(
        '<div class="topbar"><span class="breadcrumb">RESEARCH / <b>'
        + escape(page.upper())
        + '</b></span><span class="tag">RECORDED DATA · NOT LIVE</span></div>'
    )
    try:
        service = analysis_service()
        portfolios = service.portfolios.portfolios()
        names = {p["portfolio_id"]: p["portfolio_name"] for p in portfolios}
        with st.container(key="workspace"):
            title, picker = st.columns([3, 1])
            with title:
                st.html('<div class="eyebrow">PORTiQ / ANALYTICS</div>')
                st.title(page)
                st.caption(PAGES[page])
            if "gui_next_portfolio" in st.session_state:
                st.session_state["gui_selected"] = st.session_state.pop("gui_next_portfolio")
            selected = picker.selectbox(
                "Selected portfolio",
                [None, *names],
                key="gui_selected",
                format_func=lambda identity: names.get(identity, "Choose a portfolio"),
            )
            if page == "AI Analyst":
                analyst(service, selected)
            elif page == "Overview":
                overview(service, selected)
            elif selected is None:
                st.info("Choose a portfolio to explore its recorded data.")
            elif page == "Portfolio Explorer":
                explorer(service.portfolios.snapshot(selected))
            else:
                reconciliation(service.portfolios.snapshot(selected))
            st.html(
                '<footer class="footer"><span>PORTiQ / Source-backed research</span>'
                "<span>Demonstration data. No live prices or investment "
                "recommendations.</span></footer>"
            )
    except PortiqError:
        st.error("The dataset is temporarily unavailable. Please try again later.")


if __name__ == "__main__":
    main()
