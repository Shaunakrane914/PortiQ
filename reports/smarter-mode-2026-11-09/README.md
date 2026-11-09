# Smarter Answer (2 SDK) Live Verification Evidence

**Date:** 9 November 2026  
**Scope:** Per-request "Smarter answer (2 SDK)" toggle evaluation across dashboard and Streamlit UI interfaces.

---

## Overview

A new user-facing checkbox **"Smarter answer (2 SDK)"** allows users in both the web dashboard (`src/portiq/web/app.js`) and Streamlit application (`src/portiq/streamlit_app.py`) to opt into full Gemini model synthesis on demand.

### Behavior Matrix

| Control State | SDK Calls | Path & Caching | Output Format & Synthesis |
| :--- | :--- | :--- | :--- |
| **Unchecked (Default)** | 1 SDK call | Direct results fast-path; exact cache enabled if selected | Concise direct result (e.g. `COUNT(*): 13`) |
| **Checked (Smarter)** | 2 SDK calls | Local fast path & exact cache bypassed (`cache: "disabled"`) | Full Gemini model synthesis with explanation (e.g. `There are 13 portfolios in total.`) |

---

## Live Measurement Summary

Tested using real live Gemini calls against the prompt `"Count all portfolios. Return just the count."`:

### Web Dashboard (`dashboard-live.json`)

| Mode | Smarter Flag | SDK Calls | Tokens | Model Duration | Click-to-Answer | Answer Rendered |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Smarter Mode** | `true` | **2 calls** | 4,425 | 7,125 ms | 7,311 ms | `"There are 13 portfolios in total."` |
| **Direct Mode** | `false` | **1 call** | 2,310 | 4,642 ms | 4,746 ms | `"COUNT(*): 13"` |

### Streamlit Application (`streamlit-live.json`)

| Mode | Smarter Flag | SDK Calls | Tokens | Model Duration | Click-to-Answer | Answer Rendered |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Smarter Mode** | `true` | **2 calls** | 4,425 | 8,400 ms | 11,309 ms | `"There are 13 portfolios in total."` |
| **Direct Mode** | `false` | **1 call** | 2,310 | 3,740 ms | 5,069 ms | `"COUNT(*): 13"` |

---

## Verification & Test Coverage

1. **Unit & API Suite:** `tests/test_smarter_answers.py` validates that:
   - Synthesis mode blocks both direct and explicit scalar shortcuts.
   - `/api/ask` and `/api/conversation` bypass local and cache without mutating service settings.
   - Simultaneous concurrent requests from multiple users maintain strict isolation.
   - Full Python test suite: **303 passed, 1 skipped**.
2. **Browser Suite:** `tests/browser/dashboard.spec.js` and `tests/browser/streamlit.spec.js`:
   - Interactive checkbox state, help text, exclusivity over local/cache controls, and mobile layout.
   - Full Playwright test suite: **13 passed, 1 skipped**.
