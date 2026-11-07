"use strict";
const $ = (id) => document.getElementById(id);
const el = (tag, text, cls) => {
  const n = document.createElement(tag);
  if (text !== undefined && text !== null) n.textContent = String(text);
  if (cls) n.className = cls;
  return n;
};
const fmt = (v) =>
  v === null || v === undefined
    ? "Not available"
    : typeof v === "number"
      ? v.toLocaleString(undefined, { maximumFractionDigits: 4 })
      : String(v);
let page = "overview",
  selected = null,
  portfolios = [],
  session = null,
  token = "",
  snapshot = null,
  epoch = 0;
const titles = {
  overview: ["Portfolio overview", "See the allocation. Understand the basis."],
  explorer: [
    "Portfolio explorer",
    "Holdings, observations and risk — with the source in view.",
  ],
  analyst: [
    "AI analyst",
    "Ask naturally. Inspect every tool, query and calculation.",
  ],
  reconciliation: [
    "Allocation reconciliation",
    "Two valid lenses. Make their differences visible.",
  ],
  evaluation: [
    "Evaluation lab",
    "Measured evidence, with its conditions attached.",
  ],
  status: [
    "System status",
    "Understand what is local, configured and available.",
  ],
};
async function api(path, body) {
  const r = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const d = await r.json();
  if (!r.ok) {
    if (r.status === 401)
      throw new Error(
        "Access token required. Open System Status to enter your demo access token.",
      );
    throw new Error(
      typeof d.detail === "string"
        ? d.detail
        : d.response?.answer || "Request failed (HTTP " + r.status + ").",
    );
  }
  return d;
}
function card(title, kicker) {
  const c = el("article", null, "card"),
    h = el("div", null, "card-head");
  c.setAttribute("aria-label",title);
  h.append(el("h2", title), el("span", kicker || "RECORDED DATA", "kicker"));
  c.append(h);
  return c;
}
function notice(text, kind = "") {
  return el("div", text, "notice " + kind);
}
function metric(label, value, description, highlight = false) {
  const c = el("div", null, "metric" + (highlight ? " highlight" : ""));
  c.append(
    el("div", label, "label"),
    el("div", value, "value"),
    el("div", description, "description"),
  );
  return c;
}
function table(
  rows,
  columns,
  { search = false, sort = false, max = 100 } = {},
) {
  const outer = el("div");
  let query = "",
    sortKey = null,
    direction = 1;
  const wrap = el("div", null, "table-wrap"),
    t = el("table");
  wrap.append(t);
  if (search) {
    const input = el("input");
    input.type = "search";
    input.placeholder = "Search recorded rows…";
    input.setAttribute("aria-label", "Filter table rows");
    input.oninput = () => {
      query = input.value.toLowerCase();
      draw();
    };
    const bar = el("div", null, "toolbar");
    bar.append(input);
    outer.append(bar);
  }
  outer.append(wrap);
  function draw() {
    t.replaceChildren();
    const head = el("thead"),
      tr = el("tr");
    for (const [key, label] of columns) {
      const th = el("th");
      if (sort) {
        const b = el(
          "button",
          label + (sortKey === key ? (direction === 1 ? " ↑" : " ↓") : " ↕"),
        );
        b.onclick = () => {
          direction = sortKey === key ? -direction : 1;
          sortKey = key;
          draw();
        };
        th.append(b);
      } else th.textContent = label;
      tr.append(th);
    }
    head.append(tr);
    t.append(head);
    const body = el("tbody");
    let data = rows.filter((r) =>
      Object.values(r).some((v) =>
        String(v ?? "")
          .toLowerCase()
          .includes(query),
      ),
    );
    if (sortKey)
      data = [...data].sort((a, b) => {
        const x = a[sortKey],
          y = b[sortKey];
        return (
          direction *
          (x === null
            ? 1
            : y === null
              ? -1
              : Number.isFinite(Number(x)) && Number.isFinite(Number(y))
                ? Number(x) - Number(y)
                : String(x).localeCompare(String(y)))
        );
      });
    for (const row of data.slice(0, max)) {
      const r = el("tr");
      for (const [key] of columns) r.append(el("td", fmt(row[key])));
      body.append(r);
    }
    if (!data.length) {
      const r = el("tr"),
        td = el("td", "No recorded rows match this view.");
      td.colSpan = columns.length;
      r.append(td);
      body.append(r);
    }
    t.append(body);
    if (data.length > max)
      outer.setAttribute("aria-label", `Showing ${max} of ${data.length} rows`);
  }
  draw();
  return outer;
}
const ns = "http://www.w3.org/2000/svg";
function svgNode(tag, attrs, text) {
  const n = document.createElementNS(ns, tag);
  for (const [k, v] of Object.entries(attrs || {}))
    n.setAttribute(k, String(v));
  if (text !== undefined) n.textContent = String(text);
  return n;
}
function bars(data) {
  const svg = svgNode("svg", {
    viewBox: `0 0 480 ${Math.max(90, data.length * 42 + 20)}`,
    class: "chart",
    role: "img",
    "aria-label": "Equity sector allocation as percentages",
  });
  data.forEach(([name, value], i) => {
    const y = i * 42 + 18;
    svg.append(
      svgNode("text", { x: 0, y }, name),
      svgNode("rect", {
        x: 0,
        y: y + 8,
        width: 400,
        height: 9,
        rx: 3,
        fill: "#edf1ed",
      }),
      svgNode("rect", {
        x: 0,
        y: y + 8,
        width: Math.max(0, Math.min(100, Number(value))) * 4,
        height: 9,
        rx: 3,
        fill: i === 0 ? "#16786c" : "#83b5a5",
      }),
      svgNode(
        "text",
        { x: 475, y, "text-anchor": "end" },
        Number(value).toFixed(2) + "%",
      ),
    );
  });
  return svg;
}
function navChart(rows) {
  const svg = svgNode("svg", {
    viewBox: "0 0 500 160",
    class: "chart",
    role: "img",
    "aria-label": "Recorded NAV observations",
  });
  if (rows.length < 2) {
    return el(
      "p",
      "At least two recorded observations are needed for a trend view.",
      "empty",
    );
  }
  const data = rows.map((r) => Number(r.nav)),
    lo = Math.min(...data),
    hi = Math.max(...data),
    span = hi - lo || 1;
  const points = data
    .map(
      (v, i) =>
        `${35 + (i * 430) / (data.length - 1)},${120 - ((v - lo) / span) * 90}`,
    )
    .join(" ");
  svg.append(
    svgNode("line", { x1: 35, y1: 125, x2: 465, y2: 125, stroke: "#dce3df" }),
    svgNode("polyline", {
      points,
      fill: "none",
      stroke: "#16786c",
      "stroke-width": 2,
    }),
    svgNode("text", { x: 0, y: 25 }, fmt(hi)),
    svgNode("text", { x: 0, y: 125 }, fmt(lo)),
    svgNode("text", { x: 35, y: 150 }, rows[0].performance_date),
    svgNode(
      "text",
      { x: 465, y: 150, "text-anchor": "end" },
      rows.at(-1).performance_date,
    ),
  );
  return svg;
}
function warnings(items) {
  const box = el("div");
  for (const n of items)
    box.append(notice(n.kind.toUpperCase() + " · " + n.message));
  return box;
}
async function getSnapshot() {
  if (!selected) throw new Error("Select a portfolio first.");
  snapshot = await api("/api/portfolios/" + selected);
  return snapshot;
}
async function overview() {
  const d = await api("/api/overview");
  const root = el("div"),
    metrics = el("div", null, "metrics");
  metrics.append(
    metric(
      "Portfolio universe",
      d.portfolio_count,
      "Distinct recorded portfolios",
      true,
    ),
    metric("Active mandates", d.active_count, "Recorded status = Active"),
    metric(
      "Listed holdings",
      d.holding_count,
      "Positions across the supplied universe",
    ),
    metric("Aggregate AUM", "Unavailable", "Currency basis is unspecified"),
  );
  root.append(metrics);
  const grid = el("div", null, "grid"),
    ex = card("Equity sector allocation", "SELECTED PORTFOLIO"),
    scope = card("Research scope", "CALCULATION NOTES");
  if (selected) {
    const s = await getSnapshot();
    ex.append(el("p", s.portfolio.portfolio_name));
    ex.append(
      s.exposure
        ? bars(Object.entries(s.exposure.sectors))
        : el("p", "Equity exposure is undefined for this portfolio.", "empty"),
    );
    ex.append(
      el(
        "p",
        "Denominator: total recorded Stock weight. Bonds excluded.",
        "caption",
      ),
    );
  }
  scope.append(
    notice(
      "Dataset observations are historical and sparse. No price, return or risk value is represented as live.",
      "info",
    ),
    el("p", d.aum_basis),
    el(
      "p",
      "Recorded holding weights and reconstructed quote values are separate views. Differences do not establish which convention is correct.",
    ),
    el(
      "p",
      "Select a portfolio to inspect its sources and data-quality notes.",
    ),
  );
  grid.append(ex, scope);
  root.append(grid);
  const universe = card("The portfolio universe", "RECORDED MANDATES");
  universe.append(
    table(
      d.portfolios,
      [
        ["portfolio_name", "Portfolio"],
        ["status", "Status"],
        ["strategy_type", "Strategy"],
        ["target_risk_level", "Target risk"],
        ["total_aum", "Recorded AUM · currency unknown"],
      ],
      { search: true, sort: true },
    ),
  );
  root.append(universe);
  return root;
}
async function explorer() {
  const s = await getSnapshot(),
    root = el("div"),
    p = s.portfolio,
    metrics = el("div", null, "metrics");
  metrics.append(
    metric("Status", p.status, p.strategy_type, true),
    metric(
      "Recorded AUM",
      fmt(p.total_aum),
      "Currency / valuation date unspecified",
    ),
    metric(
      "Holdings",
      s.holdings.length,
      "Listed positions; not the whole AUM",
    ),
    metric(
      "Target risk",
      p.target_risk_level,
      p.benchmark_index || "Benchmark not recorded",
    ),
  );
  root.append(metrics);
  const grid = el("div", null, "grid"),
    ex = card("Equity sector exposure", "EQUITY DENOMINATOR"),
    comp = card("Recorded asset composition", "WHOLE-PORTFOLIO WEIGHTS");
  ex.append(
    s.exposure
      ? bars(Object.entries(s.exposure.sectors))
      : el("p", "No positive equity denominator.", "empty"),
  );
  comp.append(
    table(
      Object.entries(s.composition_percent).map(([asset, weight]) => ({
        asset,
        weight: fmt(Number(weight)) + "%",
      })),
      [
        ["asset", "Asset type"],
        ["weight", "Recorded weight"],
      ],
    ),
    el(
      "p",
      "Denominator: recorded whole-portfolio weight (1.0). Unrepresented weight: " +
        fmt(s.reconciliation.unrepresented_percent) +
        "%. No missing weight is inferred to be cash.",
      "caption",
    ),
  );
  grid.append(ex, comp);
  root.append(grid);
  const h = card("Holdings", "SOURCE: HOLDINGS + SECURITIES");
  h.append(
    table(
      s.holdings,
      [
        ["symbol", "Symbol"],
        ["company_name", "Name"],
        ["asset_type", "Type"],
        ["quantity", "Quantity"],
        ["current_weight", "Recorded weight · fraction"],
        ["current_price", "Quote"],
        ["currency", "Currency"],
        ["cost_basis", "Recorded cost basis"],
      ],
      { search: true, sort: true },
    ),
  );
  root.append(h);
  const perf = card("Recorded performance", "SOURCE: PORTFOLIO_PERFORMANCE");
  perf.append(
    navChart(s.performance),
    el(
      "p",
      "Connected recorded NAV observations; no invented dates or interpolated values. NAV units are unspecified.",
      "caption",
    ),
    table(s.performance, [
      ["performance_date", "Date"],
      ["nav", "NAV"],
      ["total_return_1y", "Stored 1y return"],
      ["sharpe_ratio", "Sharpe"],
      ["max_drawdown", "Stored max drawdown"],
    ]),
  );
  root.append(perf);
  const risk = card("Risk observations", "LATEST AVAILABLE FIRST");
  risk.append(
    table(s.risk, [
      ["calculation_date", "Calculation date"],
      ["var_95", "Stored VaR 95"],
      ["beta", "Beta"],
      ["tracking_error", "Tracking error"],
      ["sortino_ratio", "Sortino"],
    ]),
  );
  root.append(risk);
  const price = card("Historical price observations", "NO LIVE MARKET FEED");
  price.append(
    table(
      s.prices,
      [
        ["price_date", "Observed date"],
        ["symbol", "Symbol"],
        ["close_price", "Close"],
        ["currency", "Currency"],
      ],
      { search: true, sort: true },
    ),
  );
  root.append(price);
  const q = card("Data-quality review", "CONTEXT BEFORE CONCLUSIONS");
  q.append(warnings(s.warnings));
  root.append(q);
  return root;
}
function csvValue(v) {
  let s = String(v ?? "");
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
  return '"' + s.replaceAll('"', '""') + '"';
}
async function reconciliation() {
  const s = await getSnapshot(),
    r = s.reconciliation,
    root = el("div"),
    metrics = el("div", null, "metrics");
  metrics.append(
    metric(
      "Recorded total",
      fmt(r.recorded_total_percent) + "%",
      "Listed current_weight × 100",
      true,
    ),
    metric(
      "Unrepresented",
      fmt(r.unrepresented_percent) + "%",
      "Not inferred cash",
    ),
    metric(
      "Excess recorded",
      fmt(r.overweight_percent) + "%",
      "Weight above a total of 100%",
    ),
    metric(
      "Quoted position value",
      r.quoted_total_value ? fmt(Number(r.quoted_total_value)) : "Unavailable",
      r.currency || "No defensible combined currency basis",
    ),
  );
  root.append(metrics);
  const method = card("Read the denominator first", "METHODOLOGY");
  method.append(
    el("p", r.methodology),
    el("p", "Source columns: " + r.source_columns.join(", "), "caption"),
    warnings(r.warnings),
  );
  root.append(method);
  const sectors = card("Sector comparison", "PERCENTAGE POINTS");
  sectors.append(
    table(
      r.sectors,
      [
        ["sector", "Sector / asset group"],
        ["recorded_percent", "Recorded %"],
        ["reconstructed_percent", "Reconstructed %"],
        ["difference_pp", "Difference pp"],
      ],
      { sort: true },
    ),
  );
  root.append(sectors);
  const holdings = card("Holding-level review", "IDENTIFIED BY HOLDING ID");
  holdings.append(
    table(
      r.rows,
      [
        ["holding_id", "ID"],
        ["symbol", "Symbol"],
        ["currency", "Currency"],
        ["recorded_percent", "Recorded %"],
        ["position_value", "Quote value"],
        ["reconstructed_percent", "Reconstructed %"],
        ["difference_pp", "Difference pp"],
      ],
      { search: true, sort: true },
    ),
  );
  const button = el("button", "Download review CSV", "button secondary");
  button.onclick = () => {
    const columns = [
      "holding_id",
      "symbol",
      "currency",
      "recorded_percent",
      "position_value",
      "reconstructed_percent",
      "difference_pp",
    ];
    const text = [
      columns.map(csvValue).join(","),
      ...r.rows.map((row) => columns.map((k) => csvValue(row[k])).join(",")),
      "",
      csvValue("Methodology"),
      csvValue(r.methodology),
    ].join("\r\n");
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/csv;charset=utf-8" }),
    );
    const a = el("a");
    a.href = url;
    a.download = "portiq-reconciliation-" + selected + ".csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  holdings.append(button);
  root.append(holdings);
  return root;
}
const messages = [];
async function analyst() {
  const root = el("div"),
    c = card("A conversation with evidence", "SESSION MEMORY · MAX 8 TURNS");
  c.append(
    notice(
      "Local capabilities use no model. Other questions use genuine Gemini function calling. Selected portfolio context is explicit; unclear references require clarification.",
      "info",
    ),
  );
  const log = el("div", null, "messages");
  log.setAttribute("role", "log");
  for (const n of messages) log.append(n);
  c.append(log);
  const chips = el("div", null, "chips");
  for (const q of [
    "Count all portfolios",
    "Show holdings for the selected portfolio",
    "Calculate sector exposure for the selected portfolio",
    "What is its sector exposure?",
  ]) {
    const b = el("button", q, "chip");
    b.onclick = () => {
      input.value = q;
      input.focus();
    };
    chips.append(b);
  }
  c.append(chips);
  const form = el("form"),
    input = el("textarea");
  input.placeholder = "Ask about holdings, exposure or recorded observations…";
  input.required = true;
  input.maxLength = 3500;
  input.setAttribute("aria-label", "Ask PortiQ");
  const controls = el("div", null, "toolbar"),
    strategy = el("select");
  strategy.setAttribute("aria-label", "Execution strategy");
  for (const [val, label] of [
    ["existing", "Existing Gemini orchestration"],
    ["one-call", "Experimental one-call planner"],
  ]) {
    const o = el("option", label);
    o.value = val;
    strategy.append(o);
  }
  const local = el("input");
  local.type = "checkbox";
  local.checked = true;
  const cache = el("input");
  cache.type = "checkbox";
  cache.checked = true;
  const lab = (text, i) => {
    const l = el("label");
    l.append(i, document.createTextNode(" " + text));
    return l;
  };
  controls.append(
    strategy,
    lab("Local fast path", local),
    lab("Exact cache", cache),
  );
  const bottom = el("div", null, "form-bottom"),
    send = el("button", "Analyze →", "button");
  send.type = "submit";
  const reset = el("button", "New conversation", "button secondary");
  reset.type = "button";
  reset.onclick = () => {
    session = null;
    messages.splice(0);
    log.replaceChildren();
  };
  bottom.append(reset, send);
  form.append(input, controls, bottom);
  c.append(form);
  root.append(c);
  form.onsubmit = async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) return;
    send.disabled = true;
    reset.disabled = true;
    const user = el("div", null, "message user");
    user.append(el("div", "YOU", "kicker"), el("p", question));
    messages.push(user);
    log.append(user);
    input.value = "";
    try {
      const d = await api("/api/conversation", {
        question,
        session_id: session,
        selected_portfolio: selected,
        strategy: strategy.value,
        local: local.checked,
        cache: cache.checked,
      });
      session = d.session_id;
      const a = d.response;
      selected = a.context_portfolio;
      $("portfolio").value = selected || "";
      const block = el("div", null, "message");
      block.append(
        el("div", a.execution_source.toUpperCase(), "kicker"),
        el("pre", a.answer,"answer"),
      );
      const serviceMs = a.provider_metrics.reduce(
          (n, m) => n + m.service_ms,
          0,
        ),
        paceMs = a.provider_metrics.reduce((n, m) => n + m.pacing_ms, 0);
      block.append(
        el(
          "div",
          `${a.status} · ${a.api_calls} SDK calls · ${a.tokens} reported tokens · ${(a.duration_ms / 1000).toFixed(2)}s total · ${(serviceMs / 1000).toFixed(2)}s service · ${(paceMs / 1000).toFixed(2)}s pacing · cache ${a.cache} · ${a.model}`,
          "meta",
        ),
      );
      for (const t of a.tools) {
        const details = el("details");
        details.append(
          el(
            "summary",
            t.tool +
              (t.error ? " · needs clarification" : " · validated result"),
          ),
        );
        if (t.error) details.append(el("p", t.error));
        if (t.result?.sql) details.append(el("pre", t.result.sql));
        if (t.result?.rows)
          details.append(
            table(
              t.result.rows.map((row) =>
                Object.fromEntries(
                  t.result.columns.map((col, i) => [String(i), row[i]]),
                ),
              ),
              t.result.columns.map((col,i) => [String(i), col]),
              { max: 40 },
            ),
          );
        if (t.result?.portfolio_name)
          details.append(
            el("p", t.result.portfolio_name + " · " + t.result.basis),
          );
        block.append(details);
      }
      messages.push(block);
      log.append(block);
    } catch (e) {
      const n = notice(e.message, "error");
      messages.push(n);
      log.append(n);
    } finally {
      send.disabled = false;
      reset.disabled = false;
      input.focus();
    }
  };
  return root;
}
async function evaluation() {
  const d = await api("/api/evaluation/summary"),
    root = el("div");
  root.append(
    notice(
      "Archived regression evidence, not a live check. These questions were author-created or supplied, have been observed, and are not externally blind. This page does not launch API-consuming evaluations.",
      "info",
    ),
  );
  for (const r of d.reports) {
    const c = card(r.release + " / " + r.name, "ARCHIVED FRESH RUN"),
      m = el("div", null, "statline");
    for (const [label, value] of [
      ["Strict pass", r.passed + " / " + r.total],
      ["Answer", r.answer_correct + " / " + r.total],
      ["Routing", r.routing_correct + " / " + r.total],
      ["Narrative coverage", r.narrative_checked + " checked"],
      ["SDK calls", r.api_calls],
      ["Tokens", r.tokens],
    ]) {
      const x = el("div", label);
      x.prepend(el("strong", fmt(value)));
      m.append(x);
    }
    c.append(
      m,
      el(
        "p",
        `${r.timestamp_utc} · ${r.model} · cache ${r.cache} · mean ${(r.mean_ms / 1000).toFixed(2)}s (pacing included)`,
        "caption",
      ),
    );
    const detail = el("details");
    detail.append(
      el("summary", "Dataset and runtime provenance"),
      el(
        "pre",
        JSON.stringify(
          { dataset_sha256: r.source_sha256, runtime_sha256: r.runtime_sha256 },
          null,
          2,
        ),
      ),
    );
    c.append(detail);
    root.append(c);
  }
  return root;
}
async function status() {
  const root = el("div"),
    auth = card("Demo access", "OPTIONAL SERVER ACCESS CONTROL"),
    form = el("form", null, "toolbar"),
    input = el("input");
  input.type = "password";
  input.placeholder = "Demo access token (not Gemini key)";
  input.setAttribute("aria-label", "Demo access token");
  const b = el("button", "Use token", "button");
  form.append(input, b);
  form.onsubmit = async (e) => {
    e.preventDefault();
    token = input.value;
    input.value = "";
    if (!portfolios.length) await boot();
    else await load();
  };
  auth.append(
    el(
      "p",
      "Leave empty for an unprotected local demo. Token stays in this page's memory; Gemini credentials remain on the server.",
    ),
    form,
  );
  root.append(auth);
  try {
    const [health, about, cache] = await Promise.all([
      api("/api/health"),
      api("/api/about"),
      api("/api/cache"),
    ]);
    const c = card("Runtime readiness", "LOCAL SYSTEM"),
      kv = el("div", null, "key-grid");
    for (const [k, v] of Object.entries({
      ...health,
      ...about,
      cache_entries: cache.size,
      cache_ttl_seconds: cache.ttl_seconds,
    })) {
      const x = el("div");
      x.append(el("small", k.replaceAll("_", " ")), el("strong", fmt(v)));
      kv.append(x);
    }
    const clear = el("button", "Clear exact-match cache", "button secondary");
    clear.onclick = async () => {
      try {
        await api("/api/cache/clear", {});
        load();
      } catch (e) {
        $("error").textContent = e.message;
        $("error").hidden = false;
      }
    };
    c.append(
      kv,
      el(
        "p",
        "One worker. Bounded in-memory sessions. Optional bearer access control. No claim of multi-tenant production security.",
        "caption",
      ),
      clear,
    );
    root.append(c);
  } catch (e) {
    root.append(notice(e.message, "error"));
  }
  return root;
}
async function load() {
  const run = ++epoch;
  $("error").hidden = true;
  $("loading").hidden = false;
  $("content").replaceChildren();
  $("title").textContent = titles[page][0];
  $("subtitle").textContent = titles[page][1];
  $("crumb").textContent = page.toUpperCase();
  document.querySelectorAll("[data-page]").forEach((b) => {
    if (b.dataset.page === page) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  try {
    const content = await {
      overview,
      explorer,
      analyst,
      reconciliation,
      evaluation,
      status,
    }[page]();
    if (run === epoch) $("content").replaceChildren(content);
  } catch (e) {
    if (run === epoch) {
      $("error").textContent = e.message;
      $("error").hidden = false;
      $("content").replaceChildren();
    }
  } finally {
    if (run === epoch) $("loading").hidden = true;
  }
}
async function boot() {
  try {
    const d = await api("/api/portfolios");
    portfolios = d.records;
    for (const p of portfolios) {
      const o = el("option", p.portfolio_name);
      o.value = p.portfolio_id;
      $("portfolio").append(o);
    }
    selected = portfolios[0]?.portfolio_id ?? null;
    $("portfolio").value = selected || "";
  } catch (e) {
    page = "status";
  }
  document.querySelectorAll("[data-page]").forEach(
    (b) =>
      (b.onclick = () => {
        page = b.dataset.page;
        location.hash = page;
        load();
      }),
  );
  $("portfolio").onchange = () => {
    selected = $("portfolio").value ? Number($("portfolio").value) : null;
    load();
  };
  if (titles[location.hash.slice(1)]) page = location.hash.slice(1);
  load();
}
boot();
