const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[char]));
}

async function api(path, options) {
  const response = await fetch(path, options);
  if (response.status === 401) {
    location.href = "/login";
    throw new Error("auth");
  }
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

function bars(rows, labelKey, valueKey, format) {
  const max = Math.max(...rows.map((row) => Number(row[valueKey]) || 0), 1);
  return rows.map((row) => {
    const value = Number(row[valueKey]) || 0;
    const width = Math.max(2, Math.round((100 * value) / max));
    const shown = format ? format(value, row) : value.toLocaleString();
    return `<div class="bar-row"><span class="bar-label">${esc(row[labelKey])}</span><span class="bar-track"><span class="bar-fill" style="width:${width}%"></span></span><span class="bar-val">${esc(shown)}</span></div>`;
  }).join("");
}

function stat(label, value) {
  return `<article class="stat"><span>${esc(label)}</span><b>${esc(value)}</b></article>`;
}

function table(headers, rows) {
  const head = headers.map((header) => `<th>${esc(header)}</th>`).join("");
  const body = rows.map((row) => `<tr>${row.map((cell) => `<td>${esc(cell)}</td>`).join("")}</tr>`).join("");
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

async function metric(name) {
  return api(`/api/metric?name=${encodeURIComponent(name)}`);
}

async function renderOverview() {
  const kpi = (await metric("kpi_summary")).rows[0];
  document.getElementById("kpis").innerHTML = [
    stat("Net sales", money.format(kpi.net_sales)),
    stat("Gross margin", `${kpi.margin_pct}%`),
    stat("Trade rate", `${kpi.trade_pct}%`),
    stat("Open pipeline", money.format(kpi.open_pipeline)),
    stat("Win rate", `${kpi.win_rate}%`),
    stat("Activity conversion", `${kpi.conversion_pct}%`),
  ].join("");
  const funnel = (await metric("commercial_funnel")).rows[0];
  document.getElementById("funnel").innerHTML = [
    stat("Activities", funnel.activities.toLocaleString()),
    stat("Opportunities", funnel.opportunities.toLocaleString()),
    stat("Won", funnel.won.toLocaleString()),
    stat("Incremental net", money.format(funnel.incremental_net)),
  ].join("");
  const channels = await metric("net_by_channel");
  document.getElementById("channels").innerHTML = bars(channels.rows, "channel", "net_sales", (value) => money.format(value));
  const season = await metric("season_index");
  document.getElementById("season").innerHTML = bars(season.rows, "invoice_month", "index_vs_january", (value) => `${value}`);
  const halloween = await metric("halloween_window");
  document.getElementById("halloween").innerHTML = bars(halloween.rows, "season_window", "net_sales", (value) => money.format(value));
}

async function renderCommercial() {
  const pipeline = await metric("pipeline_by_stage");
  document.getElementById("pipeline").innerHTML = bars(pipeline.rows, "stage", "expected_net", (value) => money.format(value));
  const win = await metric("win_rate_by_channel");
  document.getElementById("win").innerHTML = bars(win.rows, "channel", "win_rate", (value) => `${value}%`);
  const conversion = await metric("activity_conversion");
  document.getElementById("conversion").innerHTML = bars(conversion.rows, "channel", "conversion_pct", (value) => `${value}%`);
  const realization = await metric("realization_by_channel");
  document.getElementById("realization").innerHTML = bars(
    realization.rows,
    "channel",
    "net_sales",
    (value, row) => `${money.format(value)} · ${row.realization_pct}%`
  );
  const age = await metric("pipeline_age");
  document.getElementById("age").innerHTML = bars(age.rows, "age_band", "expected_net", (value) => money.format(value));
  const stages = await metric("stage_conversion");
  document.getElementById("stages").innerHTML = bars(stages.rows, "stage", "share_pct", (value) => `${value}%`);
  const scorecard = await metric("account_scorecard");
  document.getElementById("scorecard").innerHTML = table(
    ["Account", "Channel", "Net", "Trade", "Win rate", "Open pipeline", "Last activity"],
    scorecard.rows.map((row) => [
      row.account_name,
      row.channel,
      money.format(row.net_sales),
      `${row.trade_pct}%`,
      `${row.win_rate}%`,
      money.format(row.open_pipeline),
      row.last_activity,
    ])
  );
}

async function renderAnalytics() {
  const families = await metric("net_by_family");
  document.getElementById("families").innerHTML = bars(families.rows, "family", "net_sales", (value) => money.format(value));
  const months = await metric("net_by_month");
  document.getElementById("months").innerHTML = bars(months.rows, "month", "net_sales", (value) => money.format(value));
  const margin = await metric("margin_by_family");
  document.getElementById("margin").innerHTML = bars(margin.rows, "family", "margin_pct", (value) => `${value}%`);
  const trade = await metric("trade_by_channel");
  document.getElementById("trade").innerHTML = bars(trade.rows, "channel", "trade_pct", (value) => `${value}%`);
  const waterfall = await metric("waterfall_by_channel");
  document.getElementById("waterfall").innerHTML = table(
    ["Channel", "Gross", "Trade", "Net", "COGS", "Margin"],
    waterfall.rows.map((row) => [
      row.channel,
      money.format(row.gross_sales),
      money.format(row.trade_spend),
      money.format(row.net_sales),
      money.format(row.cogs),
      money.format(row.margin),
    ])
  );
  const mix = await metric("family_mix_by_quarter");
  document.getElementById("mix").innerHTML = table(
    ["Quarter", "Family", "Net"],
    mix.rows.map((row) => [row.quarter, row.family, money.format(row.net_sales)])
  );
  const cells = await metric("region_by_channel");
  document.getElementById("region-channel").innerHTML = table(
    ["Region", "Channel", "Net"],
    cells.rows.map((row) => [row.region, row.channel, money.format(row.net_sales)])
  );
  const skus = await metric("sku_rank");
  document.getElementById("skus").innerHTML = table(
    ["Family", "SKU", "Net", "Units"],
    skus.rows.map((row) => [row.family, row.sku_name, money.format(row.net_sales), Number(row.units).toLocaleString()])
  );
}

function renderAudit(rows) {
  if (!rows.length) {
    document.getElementById("audit").innerHTML = "<p class='fine'>No governed questions yet.</p>";
    return;
  }
  const body = rows.map((row) => `<tr><td>${esc(row.ts)}</td><td>${esc(row.username)}</td><td>${esc(row.account_scope)}</td><td>${esc(row.question)}</td><td>${esc(row.route)}</td><td>${esc(row.metric || "")}</td><td>${esc(row.row_count)}</td></tr>`).join("");
  document.getElementById("audit").innerHTML = `<table><thead><tr><th>When</th><th>User</th><th>Scope</th><th>Question</th><th>Route</th><th>Metric</th><th>Rows</th></tr></thead><tbody>${body}</tbody></table>`;
}

async function loadAudit() {
  const payload = await api("/api/audit");
  renderAudit(payload.rows);
}

function moneyOrBlank(value, unit) {
  if (value === null || value === undefined) return "No figure loaded";
  if (String(unit).includes("percent")) return `${value}%`;
  if (String(unit).includes("people")) return Number(value).toLocaleString();
  return `${Number(value).toLocaleString()} ${unit}`;
}

async function renderMarket() {
  const payload = await metric("public_landscape");
  const body = payload.rows.map((row) => `<tr><td>${esc(row.group_name)}</td><td>${esc(row.entity)}</td><td>${esc(row.metric)}</td><td>${esc(moneyOrBlank(row.value_num, row.unit))}</td><td>${esc(row.period)}</td><td>${esc(row.scope_note)}</td><td><a href="${esc(row.source_url)}">${esc(row.source)}</a></td></tr>`).join("");
  document.getElementById("market-table").innerHTML = `<table><thead><tr><th>Group</th><th>Entity</th><th>Metric</th><th>Published value</th><th>Period</th><th>Scope</th><th>Source</th></tr></thead><tbody>${body}</tbody></table>`;
}

function renderPlan(plan) {
  const phases = plan.phases.map((phase) => `<article class="card"><p class="kicker">${esc(phase.days)}</p><h3>${esc(phase.theme)}</h3><ul>${phase.bullets.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></article>`).join("");
  const nonGoals = plan.non_goals.map((item) => `<li>${esc(item)}</li>`).join("");
  document.getElementById("plan").innerHTML = `<h2 style="margin-top:24px">${esc(plan.title)}</h2><p class="fine">${esc(plan.subtitle)}</p><div class="grid">${phases}</div><article class="panel"><h3>Non-goals</h3><ul>${nonGoals}</ul></article>`;
}

async function renderLab() {
  const plan = await api("/api/lab/plan");
  renderPlan(plan);
  const status = await api("/api/session");
  const databricks = status.databricks;
  const snowflake = status.snowflake;
  const databricksDetail = databricks.configured
    ? `Databricks ${warehouseStatus(databricks)}`
    : `Databricks is not attached. Missing ${databricks.missing.join(", ")}`;
  const snowflakeDetail = snowflake.configured
    ? `Snowflake ${snowflake.database}.${snowflake.schema}`
    : `Snowflake is not attached. Missing ${snowflake.missing.join(", ")}`;
  document.getElementById("lab-out").textContent = `${databricksDetail}. ${snowflakeDetail}. Active backend ${status.backend}.`;
}

async function renderCatalog() {
  const payload = await api("/api/catalog");
  const body = payload.layers.map((row) => `<tr><td>${esc(row.layer)}</td><td>${esc(row.table)}</td><td>${esc(row.rows.toLocaleString())}</td><td>${esc(row.note)}</td></tr>`).join("");
  document.getElementById("layers").innerHTML = `<article class="panel"><table><thead><tr><th>Layer</th><th>Table</th><th>Rows</th><th>Meaning</th></tr></thead><tbody>${body}</tbody></table></article>`;
  const metrics = Object.entries(payload.metrics).map(([name, description]) => `<tr><td><code>${esc(name)}</code></td><td>${esc(description)}</td></tr>`).join("");
  document.getElementById("metric-list").innerHTML = `<table><thead><tr><th>Metric</th><th>Definition</th></tr></thead><tbody>${metrics}</tbody></table>`;
}

function showAnswer(element, payload) {
  const lines = [payload.answer || payload.error || ""];
  if (payload.engine) lines.push("", `Engine: ${payload.engine}`);
  if (payload.sql) lines.push("", payload.sql, `Params: ${JSON.stringify(payload.params)}`);
  if (payload.rows && payload.rows.length) lines.push("", JSON.stringify(payload.rows.slice(0, 8), null, 2));
  element.textContent = lines.join("\n");
}

const loaded = {};
async function show(tab) {
  document.querySelectorAll("nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tab);
  });
  document.querySelectorAll(".tab").forEach((section) => {
    section.hidden = section.id !== tab;
  });
  if (loaded[tab]) return;
  if (tab === "overview") await renderOverview();
  if (tab === "commercial") await renderCommercial();
  if (tab === "analytics") await renderAnalytics();
  if (tab === "market") await renderMarket();
  if (tab === "assistant") await loadAudit();
  if (tab === "lab") await renderLab();
  if (tab === "catalog") await renderCatalog();
  loaded[tab] = true;
}

function warehouseStatus(warehouse) {
  const where = warehouse.catalog === "(workspace default)" ? warehouse.schema : `${warehouse.catalog}.${warehouse.schema}`;
  return `Reading ${where}`;
}

function showBackendNote(text) {
  const note = document.getElementById("dbx");
  note.hidden = !text;
  note.textContent = text || "";
}

async function chooseBackend(backend) {
  const response = await fetch("/api/backend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ backend }),
  });
  const payload = await response.json();
  if (!response.ok) {
    const quiet = payload.missing
      ? (String(payload.error || "").includes("Snowflake")
        ? "This site reads the SQLite book. No Snowflake database is attached."
        : "This site reads the SQLite book. No Databricks warehouse is attached.")
      : (payload.error || "The warehouse did not connect.");
    showBackendNote(quiet);
    return;
  }
  location.reload();
}

async function boot() {
  const session = await api("/api/session");
  if (!session.user) {
    location.href = "/login";
    return;
  }
  document.getElementById("who").textContent = `${session.user.label} · ${session.user.username}`;
  document.querySelectorAll("#backend-switch button").forEach((button) => {
    button.classList.toggle("active", button.dataset.backend === session.backend);
    button.addEventListener("click", () => chooseBackend(button.dataset.backend));
  });
  const quietTitle = "No warehouse is attached on this host.";
  if (!session.databricks.configured) {
    const button = document.querySelector('#backend-switch button[data-backend="databricks"]');
    if (button) button.title = quietTitle;
  }
  if (!session.snowflake.configured) {
    const button = document.querySelector('#backend-switch button[data-backend="snowflake"]');
    if (button) button.title = quietTitle;
  }
  let note = "";
  if (session.backend === "databricks" && session.databricks.configured) note = warehouseStatus(session.databricks);
  if (session.backend === "snowflake" && session.snowflake.configured) {
    note = `Reading ${session.snowflake.database}.${session.snowflake.schema}`;
  }
  showBackendNote(note);
  document.getElementById("chips").innerHTML = session.examples.map((example) => `<button type="button" data-example="${esc(example)}">${esc(example)}</button>`).join("");
  document.getElementById("chips").addEventListener("click", (event) => {
    const example = event.target.dataset.example;
    if (example) document.getElementById("q-next").value = example;
  });
  document.querySelectorAll("nav button").forEach((button) => {
    button.addEventListener("click", () => show(button.dataset.tab));
  });
  document.getElementById("logout").addEventListener("click", async () => {
    await api("/api/logout", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    location.href = "/login";
  });
  document.getElementById("ask-today").addEventListener("click", async () => {
    const payload = await api("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "today", question: document.getElementById("q-today").value }),
    });
    showAnswer(document.getElementById("out-today"), payload);
  });
  document.getElementById("ask-next").addEventListener("click", async () => {
    const payload = await api("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "proposed", question: document.getElementById("q-next").value }),
    });
    showAnswer(document.getElementById("out-next"), payload);
    loaded.assistant = false;
    await loadAudit();
    loaded.assistant = true;
  });
  async function runLab(path, body) {
    const payload = await api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    document.getElementById("lab-out").textContent = JSON.stringify(payload, null, 2);
  }
  document.getElementById("run-board").addEventListener("click", () => runLab("/api/lab/board"));
  document.getElementById("run-evals").addEventListener("click", () => runLab("/api/lab/evals"));
  document.getElementById("run-compare").addEventListener("click", () => runLab("/api/lab/compare", { question: "margin by brand" }));
  document.getElementById("run-scope").addEventListener("click", () => runLab("/api/lab/scope", { metric: "net_by_channel" }));
  await show("overview");
}

boot().catch((error) => {
  if (error.message !== "auth") console.error(error);
});
