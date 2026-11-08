"""Optional Streamlit chat using the same tools, quota and session services as the CLI."""

from typing import Any

import streamlit as st

from portiq.agent import AgentResponse, render_response
from portiq.config import Settings
from portiq.database import initialize
from portiq.errors import PortiqError
from portiq.service import AnalysisService


@st.cache_resource  # type: ignore[untyped-decorator]
def analysis_service() -> AnalysisService:
    settings = Settings.from_env()
    if not settings.database.exists():
        initialize(settings.source, settings.database)
    return AnalysisService(settings)


def main() -> None:
    st.set_page_config(page_title="PortiQ Analyst", page_icon="📊")
    st.title("PortiQ AI Analyst")
    st.caption("Static demonstration data. No live prices or investment recommendations.")
    local = st.sidebar.checkbox("Local fast path", value=False)
    cached = st.sidebar.checkbox("Exact cache", value=False)
    context = st.sidebar.checkbox("Conversation context", value=False)
    if st.sidebar.button("New conversation"):
        st.session_state.pop("conversation_id", None)
        st.session_state["messages"] = []
    messages: list[dict[str, Any]] = st.session_state.setdefault("messages", [])
    for message in messages:
        with st.chat_message(message["role"]):
            st.text(message["text"])
    if question := st.chat_input(
        "Ask about portfolios, holdings or sector exposure", max_chars=4000
    ):
        messages.append({"role": "user", "text": question})
        with st.chat_message("user"):
            st.text(question)
        with st.chat_message("assistant"), st.spinner("Analyzing…"):
            try:
                result, session = analysis_service().ask(
                    question,
                    session_id=st.session_state.get("conversation_id"),
                    conversation=context,
                    local=local,
                    cached=cached,
                )
                st.session_state["conversation_id"] = session
                text = (
                    "Analysis is temporarily unavailable. Please try again later."
                    if result.status == "error"
                    else render_response(result)
                )
                st.text(text)
                with st.expander("Analysis evidence"):
                    public = AgentResponse.model_validate(result)
                    st.json({"status": public.status, "tools": [t.tool for t in public.tools]})
            except PortiqError:
                text = "Analysis is temporarily unavailable. Please try again later."
                st.error(text)
            messages.append({"role": "assistant", "text": text})
            st.session_state["messages"] = messages[-32:]


if __name__ == "__main__":
    main()
