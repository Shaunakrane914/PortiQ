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
let page = "analyst",
  selected = null,
  portfolios = [],
  session = null,
  token = "",
  snapshot = null,
  smarterAnswers = false,
  epoch = 0;
const titles = {
  overview: ["Portfolio overview", "See the allocation. Understand the basis."],
  explorer: [
    "Portfolio explorer",
    "Holdings, observations and risk — with the source in view.",
  ],
  analyst: [
    "AI Analyst",
    "Ask about your portfolios. Get answers with evidence.",
  ],
  reconciliation: [
    "Allocation reconciliation",
    "Two valid lenses. Make their differences visible.",
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
    if (r.status === 401) {
      $("access-button").hidden = false;
      if (!$("access-dialog").open) $("access-dialog").showModal();
      throw new Error("This demo requires its owner's access code.");
    }
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
  c.setAttribute("aria-label", title);
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
        fill: "var(--line)",
      }),
      svgNode("rect", {
        x: 0,
        y: y + 8,
        width: Math.max(0, Math.min(100, Number(value))) * 4,
        height: 9,
        rx: 3,
        fill: i === 0 ? "var(--navy)" : "var(--gold)",
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
    svgNode("line", {
      x1: 35,
      y1: 125,
      x2: 465,
      y2: 125,
      stroke: "var(--line)",
    }),
    svgNode("polyline", {
      points,
      fill: "none",
      stroke: "var(--navy)",
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
    metrics = el("div", null, "metrics overview-metrics");
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
    el(
      "p",
      "AUM is shown per portfolio in the table. Its currency and valuation date are unspecified.",
    ),
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
      d.portfolios.map((p) => {
        const composition =
          d.composition.find((c) => c.name === p.portfolio_name) || {};
        return {
          ...p,
          recorded_stock_percent: composition.Stock ?? null,
          recorded_bond_percent: composition.Bond ?? null,
        };
      }),
      [
        ["portfolio_name", "Portfolio"],
        ["status", "Status"],
        ["strategy_type", "Strategy"],
        ["target_risk_level", "Target risk"],
        ["total_aum", "Recorded AUM · currency unknown"],
        ["recorded_stock_percent", "Stock recorded %"],
        ["recorded_bond_percent", "Bond recorded %"],
      ],
      { search: true, sort: true },
    ),
  );
  universe.append(
    el(
      "p",
      "Stock and bond percentages use the recorded whole-portfolio weight denominator (1.0). An absent asset-class entry is shown as unavailable; no cash allocation is inferred.",
      "caption",
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
  const concentration = card(
    "Concentration at a glance",
    "EXPLICIT WEIGHT BASES",
  );
  concentration.append(
    el(
      "p",
      "Largest equity sector(s), at displayed precision: " +
        (Object.entries(s.largest_equity_sectors)
          .map(([name, value]) => name + " " + value + "%")
          .join("; ") || "Not available"),
    ),
    el(
      "p",
      "Largest recorded holding(s), including bonds: " +
        (s.largest_recorded_holdings
          .map(
            (h) =>
              h.symbol +
              " (#" +
              h.holding_id +
              ") " +
              fmt(h.current_weight * 100) +
              "%",
          )
          .join("; ") || "Not available"),
    ),
    el(
      "p",
      "Equity sectors use total Stock weight. Holding rank uses recorded current_weight across all listed assets.",
      "caption",
    ),
  );
  root.append(concentration);
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
  const largest = card(
    "Largest allocation differences",
    "ABSOLUTE PERCENTAGE POINTS",
  );
  if (r.largest_discrepancies.length)
    largest.append(
      table(r.largest_discrepancies, [
        ["holding_id", "Holding ID"],
        ["symbol", "Symbol"],
        ["recorded_percent", "Recorded %"],
        ["reconstructed_percent", "Reconstructed %"],
        ["difference_pp", "Difference pp"],
      ]),
    );
  else
    largest.append(
      el("p", "No defensible reconstructed difference is available.", "empty"),
    );
  root.append(largest);
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
function remember(message, log) {
  messages.push(message);
  log.append(message);
  while (messages.length > 50) {
    messages.shift();
    log.firstChild?.remove();
  }
}
async function analyst() {
  const root = el("div"),
    c = card("A conversation with evidence", "PORTFOLIO QUESTIONS");
  c.append(
    notice(
      "Ask about the recorded portfolio data. AI questions and relevant tool results are sent to Google Gemini; avoid entering personal or confidential information.",
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
  const controls = el("div", null, "toolbar");
  const local = el("input");
  local.type = "checkbox";
  local.checked = false;
  const cache = el("input");
  cache.type = "checkbox";
  cache.checked = false;
  const smarter = el("input");
  smarter.type = "checkbox";
  smarter.checked = smarterAnswers;
  const lab = (text, i) => {
    const l = el("label");
    l.append(i, document.createTextNode(" " + text));
    return l;
  };
  const smarterLabel = lab("Detailed AI explanation", smarter);
  smarterLabel.className = "smarter-option";
  const smarterHelp = el(
    "p",
    "Gemini synthesizes an additional explanation from the verified results. Default mode provides fast, direct results in 1 call.",
    "caption",
  );
  smarterHelp.id = "smarter-help";
  smarter.setAttribute("aria-describedby", smarterHelp.id);
  const updateMode = () => {
    smarterAnswers = smarter.checked;
    local.disabled = cache.disabled = smarter.checked;
    if (smarter.checked) local.checked = cache.checked = false;
    smarterHelp.hidden = !smarter.checked;
  };
  smarter.onchange = updateMode;
  updateMode();
  controls.append(lab("Local fast path", local), lab("Exact cache", cache), smarterLabel);
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
  form.append(input, controls, smarterHelp, bottom);
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
    remember(user, log);
    input.value = "";
    try {
      const d = await api("/api/conversation", {
        question,
        session_id: session,
        selected_portfolio: selected,
        strategy: "existing",
        local: local.checked,
        cache: cache.checked,
        smarter: smarter.checked,
      });
      session = d.session_id;
      const a = d.response;
      selected = a.context_portfolio;
      $("portfolio").value = selected || "";
      const block = el("div", null, "message");
      block.append(
        el("div", a.execution_source.toUpperCase(), "kicker"),
        el("pre", a.answer, "answer"),
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
              t.result.columns.map((col, i) => [String(i), col]),
              { max: 40 },
            ),
          );
        if (t.result?.portfolio_name)
          details.append(
            el("p", t.result.portfolio_name + " · " + t.result.basis),
          );
        block.append(details);
      }
      remember(block, log);
    } catch (e) {
      const n = notice(e.message, "error");
      remember(n, log);
    } finally {
      send.disabled = false;
      reset.disabled = false;
      input.focus();
    }
  };
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
    $("content").replaceChildren(notice(e.message, "info"));
  }
  document.querySelectorAll("[data-page]").forEach(
    (b) =>
      (b.onclick = () => {
        page = b.dataset.page;
        location.hash = page;
        load();
      }),
  );
  document.querySelector(".brand").onclick = (event) => {
    event.preventDefault();
    page = "analyst";
    location.hash = page;
    load();
  };
  $("portfolio").onchange = () => {
    selected = $("portfolio").value ? Number($("portfolio").value) : null;
    load();
  };
  if (titles[location.hash.slice(1)]) page = location.hash.slice(1);
  if (portfolios.length) load();
}
$("access-button").onclick = () => $("access-dialog").showModal();
$("access-cancel").onclick = () => $("access-dialog").close();
$("access-form").onsubmit = async (event) => {
  event.preventDefault();
  token = $("access-code").value.trim();
  $("access-code").value = "";
  $("access-error").hidden = true;
  try {
    const d = await api("/api/portfolios");
    portfolios = d.records;
    $("portfolio").replaceChildren(new Option("Choose a portfolio", ""));
    for (const p of portfolios)
      $("portfolio").append(new Option(p.portfolio_name, p.portfolio_id));
    selected = portfolios[0]?.portfolio_id ?? null;
    $("portfolio").value = selected || "";
    $("access-dialog").close();
    await load();
  } catch (e) {
    token = "";
    $("access-error").textContent = e.message;
    $("access-error").hidden = false;
  }
};
boot();
