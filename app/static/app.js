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
  if (payload.lane_note) showBackendNote(payload.lane_note);
  return payload;
}

const FAMILY_COLOR = {
  Nerds: "#7b2d8e",
  Trolli: "#3d7a12",
  SweeTarts: "#e23d8c",
  "Laffy Taffy": "#f0a202",
  Butterfinger: "#e07a1f",
  "Baby Ruth": "#8c4a2f",
  "Brach's": "#dc1a41",
  Lemonhead: "#e6b800",
};

function labeled(name) {
  const mark = typeof brandMark === "function" ? brandMark(name) : "";
  return `${mark ? `<span class="mark-slot">${mark}</span>` : ""}${esc(name)}`;
}

function familyClose(rows) {
  const grouped = new Map();
  rows.forEach((row) => {
    if (!grouped.has(row.family)) grouped.set(row.family, []);
    grouped.get(row.family).push(row);
  });
  const lines = [...grouped.entries()].map(([family, cells]) => {
    const ranked = [...cells].sort((a, b) => a.win_rate - b.win_rate);
    const weak = ranked[0];
    const strong = ranked[ranked.length - 1];
    return [family, weak.channel, pct(weak.win_rate), strong.channel, pct(strong.win_rate)];
  });
  return lines.length
    ? table(["Family", "Weakest close", "Win rate", "Strongest close", "Win rate"], lines)
    : `<p class="fine">No opportunities in this slice.</p>`;
}

function bars(rows, labelKey, valueKey, format) {
  if (!rows.length) return `<p class="fine">No rows in this slice.</p>`;
  const max = Math.max(...rows.map((row) => Math.abs(Number(row[valueKey]) || 0)), 1);
  return rows.map((row, index) => {
    const value = Number(row[valueKey]) || 0;
    const width = Math.max(2, Math.round((100 * Math.abs(value)) / max));
    const shown = format ? format(value, row) : value.toLocaleString();
    const color = FAMILY_COLOR[row[labelKey]];
    const tone = value < 0 ? " down" : "";
    const paint = color ? `background:${color};` : "";
    return `<div class="bar-row"><span class="bar-label">${labeled(row[labelKey])}</span><span class="bar-track"><span class="bar-fill${tone}" style="--w:${width}%;animation-delay:${index * 50}ms;${paint}"></span></span><span class="bar-val">${esc(shown)}</span></div>`;
  }).join("");
}

function funnelChart(row) {
  if (!row || row.activities === null || row.activities === undefined) {
    return `<p class="fine">No rows in this slice.</p>`;
  }
  const steps = [
    ["Activities", Number(row.activities) || 0],
    ["Opportunities", Number(row.opportunities) || 0],
    ["Won", Number(row.won) || 0],
  ];
  const max = Math.max(steps[0][1], 1);
  const barsHtml = steps.map(([label, value], index) => {
    const width = Math.max(28, Math.round((100 * value) / max));
    return `<div class="funnel-step"><div class="funnel-bar" style="--w:${width}%;animation-delay:${index * 80}ms"><span>${esc(label)}</span><b>${esc(value.toLocaleString())}</b></div></div>`;
  }).join("");
  return `${barsHtml}<p class="fine">Incremental invoice net ${esc(money.format(row.incremental_net || 0))} inside total net ${esc(money.format(row.net_sales || 0))}.</p>`;
}

function stackedMix(rows) {
  if (!rows.length) return `<p class="fine">No rows in this slice.</p>`;
  const groups = new Map();
  rows.forEach((row) => {
    if (!groups.has(row.quarter)) groups.set(row.quarter, []);
    groups.get(row.quarter).push(row);
  });
  const totals = [...groups.values()].map((items) => items.reduce((sum, row) => sum + Number(row.net_sales || 0), 0));
  const max = Math.max(...totals, 1);
  const families = [...new Set(rows.map((row) => row.family))];
  const legend = families.map((family) => `<span><i style="background:${FAMILY_COLOR[family] || "#dc1a41"}"></i>${esc(family)}</span>`).join("");
  const body = [...groups.entries()].map(([quarter, items]) => {
    const total = items.reduce((sum, row) => sum + Number(row.net_sales || 0), 0);
    const segs = items.map((row) => {
      const width = total ? (100 * Number(row.net_sales || 0)) / total : 0;
      return `<i class="stack-seg" style="width:${width}%;background:${FAMILY_COLOR[row.family] || "#dc1a41"}" title="${esc(row.family)}"></i>`;
    }).join("");
    const scale = Math.max(8, Math.round((100 * total) / max));
    return `<div class="stack-row"><span>${esc(quarter)}</span><span class="stack-track"><span class="stack-bar" style="width:${scale}%">${segs}</span></span><span class="bar-val">${esc(money.format(total))}</span></div>`;
  }).join("");
  return `${body}<div class="legend">${legend}</div>`;
}

function heatMap(rows) {
  if (!rows.length) return `<p class="fine">No rows in this slice.</p>`;
  const regions = [...new Set(rows.map((row) => row.region))];
  const channels = [...new Set(rows.map((row) => row.channel))];
  const lookup = new Map(rows.map((row) => [`${row.region}|${row.channel}`, Number(row.net_sales) || 0]));
  const max = Math.max(...lookup.values(), 1);
  const head = channels.map((channel) => `<span class="heat-label">${esc(channel)}</span>`).join("");
  const body = regions.map((region) => {
    const cells = channels.map((channel) => {
      const value = lookup.get(`${region}|${channel}`) || 0;
      const alpha = (0.12 + (0.88 * value) / max).toFixed(2);
      return `<span class="heat-cell" style="background:rgba(220,26,65,${alpha})"><b>${esc(money.format(value))}</b></span>`;
    }).join("");
    return `<span class="heat-label">${esc(region)}</span>${cells}`;
  }).join("");
  return `<div class="heat-grid" style="--cols:${channels.length}">${head.startsWith("<") ? `<span></span>${head}${body}` : body}</div>`;
}

function waterfallChart(rows) {
  if (!rows.length) return `<p class="fine">No rows in this slice.</p>`;
  const sum = (key) => rows.reduce((total, row) => total + (Number(row[key]) || 0), 0);
  const gross = sum("gross_sales");
  const trade = sum("trade_spend");
  const net = sum("net_sales");
  const cogs = sum("cogs");
  const margin = sum("margin");
  const ceiling = Math.max(gross, 1);
  const steps = [
    ["Gross", 0, gross, "up", gross],
    ["Trade", net, gross, "down", -trade],
    ["Net", 0, net, "total", net],
    ["COGS", margin, net, "down", -cogs],
    ["Margin", 0, margin, "total", margin],
  ];
  return `<div class="falls">${steps.map(([label, start, end, kind, value], index) => {
    const bottom = (100 * Math.min(start, end)) / ceiling;
    const height = Math.max((100 * Math.abs(end - start)) / ceiling, 1.5);
    return `<div class="fall"><i class="fall-bar ${kind}" style="bottom:${bottom}%;height:${height}%;animation-delay:${index * 70}ms"></i><span>${esc(label)}<b>${esc(money.format(value))}</b></span></div>`;
  }).join("")}</div>`;
}

function stat(label, value) {
  return `<article class="stat"><span>${esc(label)}</span><b>${esc(value)}</b></article>`;
}

function table(headers, rows) {
  const head = headers.map((header) => `<th>${esc(header)}</th>`).join("");
  const body = rows.map((row) => `<tr>${row.map((cell) => `<td>${esc(cell)}</td>`).join("")}</tr>`).join("");
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

const slices = { channel: "", region: "", subregion: "", family: "", year: "" };
let sliceTree = {};
const slicedTabs = new Set(["brief", "overview", "commercial", "analytics", "supply", "operations", "market", "assistant"]);

async function metric(name) {
  const query = new URLSearchParams({ name });
  Object.entries(slices).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  return api(`/api/metric?${query}`);
}

async function loadMetrics(names) {
  const payloads = await Promise.all(names.map((name) => metric(name)));
  return Object.fromEntries(names.map((name, index) => [name, payloads[index]]));
}

function sliceFields() {
  const fields = {};
  Object.entries(slices).forEach(([key, value]) => {
    if (value) fields[key] = value;
  });
  return fields;
}

function pct(value) {
  return value === null || value === undefined ? "—" : `${value}%`;
}

async function renderBrief(gen) {
  const query = new URLSearchParams(sliceFields());
  const [data, compete, landscape] = await Promise.all([
    loadMetrics(["kpi_summary", "call_list", "supply_service"]),
    api(`/api/compete?${query}`),
    api("/api/metric?name=public_landscape"),
  ]);
  if (!current(gen)) return;
  const kpi = data.kpi_summary.rows[0] || {};
  document.getElementById("brief-kpis").innerHTML = [
    stat("Net sales", money.format(kpi.net_sales || 0)),
    stat("Win rate", pct(kpi.win_rate)),
    stat("Open pipeline", money.format(kpi.open_pipeline || 0)),
    stat("Trade rate", pct(kpi.trade_pct)),
  ].join("");
  const calls = (data.call_list.rows || []).slice(0, 3);
  const firstDeal = calls[0] && calls[0].deals && calls[0].deals[0];
  document.getElementById("brief-calls").innerHTML = calls.length
    ? table(
      ["Account", "Open pipeline", "Why"],
      calls.map((row) => [row.account_name, money.format(row.open_pipeline), row.reason])
    ) + (firstDeal
      ? `<p class="fine">Largest open deal on ${esc(calls[0].account_name)}: ${esc(firstDeal.family)} at ${esc(firstDeal.stage)}, ${esc(money.format(firstDeal.expected_net))} expected net.</p>`
      : "")
    : `<p class="fine">No account in this slice meets the call rule.</p>`;
  const plays = (compete.plays || []).slice(0, 4);
  document.getElementById("brief-plays").innerHTML = `<p class="fine">${esc(compete.book_label || "")}</p>` + plays.map((play) => `<article class="play"><h3>${esc(play.title)}</h3><p>${esc(play.detail)}</p></article>`).join("");
  const miss = (data.supply_service.rows || [])[0];
  document.getElementById("brief-supply").innerHTML = miss
    ? `<p>${esc(miss.family)} fill is ${esc(pct(miss.fill_pct))}. ${esc(Number(miss.units_short).toLocaleString())} units were ordered and did not arrive.</p>`
    : `<p class="fine">Vendor scorecards stay on the operator book.</p>`;
  const published = landscape.rows || [];
  const orange = published.find((row) => String(row.entity || "").includes("Orangeburg"));
  const campaigns = published.filter((row) => row.group_name === "Published campaign");
  const orangeLine = orange
    ? `${orange.entity}: ${orange.value_num == null ? "not published" : `${orange.value_num} ${orange.unit}`} (${orange.period}). ${orange.scope_note}`
    : "Orangeburg is not in the published record.";
  document.getElementById("brief-public").innerHTML = `<p>${esc(orangeLine)}</p><p>${esc(String(campaigns.length))} campaigns are named. Media spend is not published, so none is scored.</p>`;
}

async function renderOverview(gen) {
  const data = await loadMetrics(["kpi_summary", "commercial_funnel", "net_by_channel", "season_index", "halloween_window"]);
  if (!current(gen)) return;
  const kpi = data.kpi_summary.rows[0] || {};
  document.getElementById("kpis").innerHTML = [
    stat("Net sales", money.format(kpi.net_sales || 0)),
    stat("Gross margin", pct(kpi.margin_pct)),
    stat("Trade rate", pct(kpi.trade_pct)),
    stat("Open pipeline", money.format(kpi.open_pipeline || 0)),
    stat("Win rate", pct(kpi.win_rate)),
    stat("Activity conversion", pct(kpi.conversion_pct)),
  ].join("");
  document.getElementById("funnel").innerHTML = funnelChart(data.commercial_funnel.rows[0]);
  document.getElementById("channels").innerHTML = bars(data.net_by_channel.rows, "channel", "net_sales", (value) => money.format(value));
  document.getElementById("season").innerHTML = bars(data.season_index.rows, "invoice_month", "index_vs_january", (value) => `${value}`);
  document.getElementById("halloween").innerHTML = bars(data.halloween_window.rows, "season_window", "net_sales", (value) => money.format(value));
}

async function renderCommercial(gen) {
  const data = await loadMetrics([
    "pipeline_by_stage",
    "win_rate_by_channel",
    "win_rate_by_region",
    "win_rate_by_subregion",
    "activity_conversion",
    "realization_by_channel",
    "pipeline_age",
    "stage_conversion",
    "activity_mix",
    "account_scorecard",
    "call_list",
  ]);
  if (!current(gen)) return;
  document.getElementById("pipeline").innerHTML = bars(data.pipeline_by_stage.rows, "stage", "expected_net", (value) => money.format(value));
  document.getElementById("win").innerHTML = bars(data.win_rate_by_channel.rows, "channel", "win_rate", (value) => `${value}%`);
  document.getElementById("win-region").innerHTML = bars(data.win_rate_by_region.rows, "region", "win_rate", (value) => `${value}%`);
  document.getElementById("win-subregion").innerHTML = bars(data.win_rate_by_subregion.rows, "subregion", "win_rate", (value) => `${value}%`);
  document.getElementById("conversion").innerHTML = bars(data.activity_conversion.rows, "channel", "conversion_pct", (value) => `${value}%`);
  document.getElementById("realization").innerHTML = bars(
    data.realization_by_channel.rows,
    "channel",
    "net_sales",
    (value, row) => `${money.format(value)} · ${row.realization_pct}%`
  );
  document.getElementById("age").innerHTML = bars(data.pipeline_age.rows, "age_band", "expected_net", (value) => money.format(value));
  document.getElementById("stages").innerHTML = bars(data.stage_conversion.rows, "stage", "share_pct", (value) => `${value}%`);
  document.getElementById("activity-mix").innerHTML = bars(data.activity_mix.rows, "activity_type", "activities", (value) => value.toLocaleString());
  const calls = data.call_list.rows;
  const deals = calls.flatMap((row) => (row.deals || []).map((deal) => [
    row.account_name,
    deal.family,
    deal.stage,
    deal.opened_date,
    money.format(deal.expected_net),
  ]));
  document.getElementById("calls").innerHTML = calls.length
    ? table(
      ["Account", "Channel", "Subregion", "Open pipeline", "Win rate", "Last activity", "Why"],
      calls.map((row) => [
        row.account_name,
        row.channel,
        row.subregion,
        money.format(row.open_pipeline),
        pct(row.win_rate),
        row.last_activity,
        row.reason,
      ])
    ) + (deals.length ? `<h3 style="margin-top:16px">Open deals</h3>${table(
      ["Account", "Family", "Stage", "Opened", "Expected net"],
      deals
    )}` : "")
    : "<p class=\"fine\">No account in this slice meets the rule.</p>";
  const scorecard = data.account_scorecard;
  document.getElementById("scorecard").innerHTML = table(
    ["Account", "Channel", "Net", "Trade", "Win rate", "Open pipeline", "Last activity"],
    scorecard.rows.map((row) => [
      row.account_name,
      row.channel,
      money.format(row.net_sales),
      pct(row.trade_pct),
      pct(row.win_rate),
      money.format(row.open_pipeline),
      row.last_activity,
    ])
  );
}

async function renderAnalytics(gen) {
  const data = await loadMetrics([
    "net_by_family",
    "net_by_month",
    "net_by_year",
    "margin_by_family",
    "trade_by_channel",
    "waterfall_by_channel",
    "family_mix_by_quarter",
    "region_by_channel",
    "subregion_by_channel",
    "top_accounts",
    "net_by_region",
    "net_by_subregion",
    "sku_rank",
    "close_by_family_channel",
  ]);
  if (!current(gen)) return;
  document.getElementById("families").innerHTML = bars(data.net_by_family.rows, "family", "net_sales", (value) => money.format(value));
  const yearly = !slices.year;
  document.getElementById("month-title").textContent = yearly ? "Net sales by fiscal year" : "Invoice month";
  document.getElementById("months").innerHTML = yearly
    ? bars(data.net_by_year.rows, "year", "net_sales", (value) => money.format(value))
    : bars(data.net_by_month.rows, "month", "net_sales", (value) => money.format(value));
  document.getElementById("margin").innerHTML = bars(data.margin_by_family.rows, "family", "margin_pct", (value) => `${value}%`);
  document.getElementById("trade").innerHTML = bars(data.trade_by_channel.rows, "channel", "trade_pct", (value) => `${value}%`);
  const waterfall = data.waterfall_by_channel;
  document.getElementById("bridge").innerHTML = waterfallChart(waterfall.rows);
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
  document.getElementById("mix").innerHTML = stackedMix(data.family_mix_by_quarter.rows);
  const geoCut = Boolean(slices.region);
  document.getElementById("heat-title").textContent = geoCut ? "Subregion by channel" : "Region by channel";
  document.getElementById("region-channel").innerHTML = heatMap((geoCut ? data.subregion_by_channel : data.region_by_channel).rows);
  document.getElementById("accounts").innerHTML = bars(data.top_accounts.rows, "account_name", "net_sales", (value) => money.format(value));
  document.getElementById("geo-title").textContent = geoCut ? "Net sales by subregion" : "Net sales by region";
  document.getElementById("regions").innerHTML = bars(
    (geoCut ? data.net_by_subregion : data.net_by_region).rows,
    geoCut ? "subregion" : "region",
    "net_sales",
    (value) => money.format(value)
  );
  const skus = data.sku_rank;
  document.getElementById("family-close").innerHTML = familyClose(data.close_by_family_channel.rows);
  document.getElementById("skus").innerHTML = table(
    ["Family", "SKU", "Net", "Units"],
    skus.rows.map((row) => [row.family, row.sku_name, money.format(row.net_sales), Number(row.units).toLocaleString()])
  );
}

function renderAudit(rows, highlightLatest) {
  if (!rows.length) {
    document.getElementById("audit").innerHTML = "<p class='fine'>No governed questions yet.</p>";
    return;
  }
  const body = rows.map((row, index) => {
    const fresh = highlightLatest && index === 0 ? " class=\"fresh\"" : "";
    return `<tr${fresh}><td>${esc(row.ts)}</td><td>${esc(row.username)}</td><td>${esc(row.account_scope)}</td><td>${esc(row.question)}</td><td>${esc(row.route)}</td><td>${esc(row.metric || "")}</td><td>${esc(row.row_count)}</td></tr>`;
  }).join("");
  document.getElementById("audit").innerHTML = `<table><thead><tr><th>When</th><th>User</th><th>Scope</th><th>Question</th><th>Route</th><th>Metric</th><th>Rows</th></tr></thead><tbody>${body}</tbody></table>`;
}

async function loadAudit(gen, highlightLatest) {
  const payload = await api("/api/audit");
  if (gen !== undefined && !current(gen)) return;
  renderAudit(payload.rows, highlightLatest);
}

function moneyOrBlank(value, unit) {
  if (value === null || value === undefined) return "No figure loaded";
  if (String(unit).includes("percent")) return `${value}%`;
  if (String(unit).includes("people")) return Number(value).toLocaleString();
  return `${Number(value).toLocaleString()} ${unit}`;
}

function publishedTable(rows) {
  const body = rows.map((row) => `<tr><td>${esc(row.group_name)}</td><td>${esc(row.entity)}</td><td>${esc(row.metric)}</td><td>${esc(moneyOrBlank(row.value_num, row.unit))}</td><td>${esc(row.period)}</td><td>${esc(row.scope_note)}</td><td><a href="${esc(row.source_url)}">${esc(row.source)}</a></td></tr>`).join("");
  return `<table><thead><tr><th>Group</th><th>Entity</th><th>Metric</th><th>Published value</th><th>Period</th><th>Scope</th><th>Source</th></tr></thead><tbody>${body}</tbody></table>`;
}

function renderCompete(brief, rows) {
  const roles = (brief.roles || []).map((role) => `<article class="role-card"><span>${esc(role.system)}</span><p>${esc(role.job)}</p></article>`).join("");
  const guesses = (brief.guesses || []).map((guess) => {
    const span = guess.high == null ? `${guess.low}+` : `${guess.low}–${guess.high}`;
    const headline = guess.point == null ? span : String(guess.point);
    const stamp = guess.kind === "stated" ? "COMPANY STATED" : "SYNTHETIC GUESS";
    return `<article class="guess ${esc(guess.kind)}"><span class="banner">${stamp}</span><h3>${esc(guess.entity)}</h3><b>${esc(headline)} ${esc(guess.unit)}</b><p class="fine">${esc(guess.method)}</p></article>`;
  }).join("");
  const arenas = (brief.arenas || []).map((arena) => {
    const marks = (arena.marks || []).map((name) => brandMark(name)).join("");
    return `<article class="arena"><p class="kicker">${esc(arena.name)}</p><h3><span class="mark-slot">${marks}</span>${esc(arena.ours)}</h3><p>Against ${esc(arena.theirs)}.</p><p class="fine">${esc(arena.fact)}</p><p>${esc(arena.press)}</p></article>`;
  }).join("");
  const plays = (brief.plays || []).map((play) => `<article class="play"><h3>${esc(play.title)}</h3><p>${esc(play.detail)}</p></article>`).join("");
  const lane = brief.lane_note ? `<p class="fine">${esc(brief.lane_note)}</p>` : "";
  document.getElementById("compete").innerHTML = `
    <div class="role-row">${roles}</div>
    ${lane}
    <p class="fine">${esc(brief.book_label || "")}</p>
    <p class="fine">${esc(brief.boundary || "")}</p>
    <h3>Published record</h3>
    <p class="fine">One table. Each row keeps its own denominator. A blank cell is a figure that was not filed.</p>
    <article class="panel">${publishedTable(rows || [])}</article>
    <h3>Private competitive guesses</h3>
    <p class="fine">Original marks on the arenas are drawings in the public brand colors, not Ferrara’s logos or pack art. Guess figures are not filings and not a syndicated share. They are not rows in the published record.</p>
    <div class="guess-grid">${guesses}</div>
    <h3>Where the brands actually meet</h3>
    <div class="arena-grid">${arenas}</div>
    <h3 style="margin-top:16px">Where to press</h3>
    <div class="play-list">${plays}</div>
    <p style="margin-top:12px"><button type="button" id="ask-genie-compete">Compare this question with Genie</button></p>
    <p class="fine">Genie is asked only this governed question. Its space is not this book.</p>`;
}

async function renderSupply(gen) {
  const data = await loadMetrics(["vendor_scorecard", "supply_service", "supply_risk"]);
  if (!current(gen)) return;
  const vendors = data.vendor_scorecard.rows;
  document.getElementById("vendor-score").innerHTML = vendors.length
    ? table(
      ["Vendor", "Role", "Fill", "On time", "Rejects", "Cost var", "Score"],
      vendors.map((row) => [
        row.vendor_name,
        row.vendor_role,
        pct(row.fill_pct),
        pct(row.on_time_pct),
        pct(row.reject_pct),
        pct(row.cost_var_pct),
        String(row.score),
      ])
    )
    : `<p class="fine">Vendor scorecards stay on the operator book.</p>`;
  document.getElementById("supply-fill").innerHTML = data.supply_service.rows.length
    ? bars(data.supply_service.rows, "family", "fill_pct", (value, row) => `${value}% · ${Number(row.units_short).toLocaleString()} short`)
    : `<p class="fine">No receipts in this slice.</p>`;
  document.getElementById("supply-risk").innerHTML = data.supply_risk.rows.length
    ? bars(data.supply_risk.rows, "family", "share_pct", (value, row) => `${value}% ${row.vendor_name}`)
    : `<p class="fine">No receipts in this slice.</p>`;
}

function publishedOrBlank(value, unit) {
  if (value === null || value === undefined) return "Not published";
  return moneyOrBlank(value, unit);
}

function opportunityTable(published, vendors, risk) {
  const lines = [];
  published.filter((row) => row.group_name === "Published facility" && row.value_num != null && String(row.unit).includes("USD")).forEach((row) => {
    lines.push(["Published", row.entity, `${publishedOrBlank(row.value_num, row.unit)}. ${row.period}. ${row.scope_note}`]);
  });
  const campaigns = published.filter((row) => row.group_name === "Published campaign");
  if (campaigns.length) {
    lines.push(["Published", "Named campaigns", `${campaigns.length} campaigns are named. Media spend is not published, so none is scored.`]);
  }
  if (vendors.length) {
    const weak = vendors[0];
    lines.push(["Synthetic book", weak.vendor_name, `Lowest vendor score in view, ${weak.score}. Fill ${weak.fill_pct}%, on time ${weak.on_time_pct}%. Not a Ferrara supplier.`]);
  }
  if (risk.length) {
    const top = risk[0];
    lines.push(["Synthetic book", top.family, `${top.vendor_name} holds ${top.share_pct}% of this family in view. Not a published supply plan.`]);
  }
  if (!vendors.length && !risk.length) {
    lines.push(["Synthetic book", "Supply gaps", "Those rows stay on the operator book."]);
  }
  return table(["Kind", "Opportunity", "What we can say"], lines);
}

function sourceTable(rows) {
  const body = rows.map((row) => [
    row.entity,
    row.metric,
    publishedOrBlank(row.value_num, row.unit),
    row.period,
    row.scope_note,
  ]);
  return table(["Name", "Published item", "Figure", "Period", "Scope"], body);
}

async function renderOperations(gen) {
  const [book, published, vendors, risk] = await Promise.all([
    metric("waterfall_by_channel"),
    metric("public_landscape"),
    metric("vendor_scorecard"),
    metric("supply_risk"),
  ]);
  if (!current(gen)) return;
  const rows = published.rows || [];
  document.getElementById("facilities").innerHTML = sourceTable(rows.filter((row) => row.group_name === "Published facility"));
  document.getElementById("campaigns").innerHTML = sourceTable(rows.filter((row) => row.group_name === "Published campaign"));
  document.getElementById("opps").innerHTML = opportunityTable(rows, vendors.rows || [], risk.rows || []);
  const pnlRows = book.rows || [];
  const sum = (key) => pnlRows.reduce((total, row) => total + (Number(row[key]) || 0), 0);
  const gross = sum("gross_sales");
  const trade = sum("trade_spend");
  const net = sum("net_sales");
  const cogs = sum("cogs");
  const margin = sum("margin");
  document.getElementById("book-pnl").innerHTML = pnlRows.length
    ? table(
      ["Line", "Amount"],
      [
        ["Gross", money.format(gross)],
        ["Trade", money.format(-trade)],
        ["Net", money.format(net)],
        ["COGS", money.format(-cogs)],
        ["Margin", money.format(margin)],
        ["Operating profit", "Not published"],
      ]
    )
    : `<p class="fine">No invoices in this slice.</p>`;
}

async function renderMarket(gen) {
  const query = new URLSearchParams();
  Object.entries(slices).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const [brief, payload] = await Promise.all([api(`/api/compete?${query}`), metric("public_landscape")]);
  if (!current(gen)) return;
  renderCompete(brief, payload.rows);
}

function renderPlan(plan) {
  const phases = plan.phases.map((phase) => `<article class="card"><p class="kicker">${esc(phase.days)}</p><h3>${esc(phase.theme)}</h3><ul>${phase.bullets.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></article>`).join("");
  const nonGoals = plan.non_goals.map((item) => `<li>${esc(item)}</li>`).join("");
  document.getElementById("plan").innerHTML = `<h2 style="margin-top:24px">${esc(plan.title)}</h2><p class="fine">${esc(plan.subtitle)}</p><div class="grid">${phases}</div><article class="panel"><h3>Non-goals</h3><ul>${nonGoals}</ul></article>`;
}

async function renderLab(gen) {
  const [plan, status] = await Promise.all([api("/api/lab/plan"), api("/api/session")]);
  if (!current(gen)) return;
  renderPlan(plan);
  const databricks = status.databricks;
  const snowflake = status.snowflake;
  const databricksDetail = databricks.configured
    ? `Databricks ${warehouseStatus(databricks)}`
    : `Databricks is not attached. Missing ${databricks.missing.join(", ")}`;
  const snowflakeDetail = snowflake.configured
    ? `Snowflake ${snowflake.database}.${snowflake.schema}`
    : `Snowflake is not attached. Missing ${snowflake.missing.join(", ")}`;
  document.getElementById("lab-out").textContent = `${databricksDetail}. ${snowflakeDetail}. ${status.lane_note || ""}`;
}

async function renderCatalog(gen) {
  const payload = await api("/api/catalog");
  if (!current(gen)) return;
  const body = payload.layers.map((row) => `<tr><td>${esc(row.layer)}</td><td>${esc(row.table)}</td><td>${esc(row.rows.toLocaleString())}</td><td>${esc(row.note)}</td></tr>`).join("");
  document.getElementById("layers").innerHTML = `<article class="panel"><table><thead><tr><th>Layer</th><th>Table</th><th>Rows</th><th>Meaning</th></tr></thead><tbody>${body}</tbody></table></article>`;
  const metrics = Object.entries(payload.metrics).map(([name, description]) => `<tr><td><code>${esc(name)}</code></td><td>${esc(description)}</td></tr>`).join("");
  document.getElementById("metric-list").innerHTML = `<table><thead><tr><th>Metric</th><th>Definition</th></tr></thead><tbody>${metrics}</tbody></table>`;
}

function formatCell(key, value) {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value) || (typeof value === "object")) return JSON.stringify(value);
  const lower = String(key).toLowerCase();
  if (typeof value === "number") {
    if (lower.includes("rate") || lower.includes("pct") || lower.includes("percent") || lower === "fill" || lower === "score") {
      return pct(value);
    }
    if (lower.includes("net") || lower.includes("sales") || lower.includes("pipeline") || lower.includes("margin") || lower.includes("trade") || lower.includes("gross") || lower.includes("cogs") || lower.includes("expected")) {
      return money.format(value);
    }
    return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return String(value);
}

function rowsTable(rows, limit = 8) {
  const sample = (rows || []).slice(0, limit);
  if (!sample.length) return "";
  const keys = Object.keys(sample[0]).filter((key) => key !== "deals");
  const head = keys.map((key) => key.replace(/_/g, " "));
  const body = sample.map((row) => keys.map((key) => formatCell(key, row[key])));
  return `<div class="row-table">${table(head, body)}</div>`;
}

function sliceLine(payload) {
  const bits = [];
  if (payload.filters && Object.keys(payload.filters).length) {
    bits.push(`Slice: ${Object.entries(payload.filters).map(([key, value]) => `${key}: ${value}`).join(", ")}`);
  }
  if (payload.skipped && payload.skipped.length) bits.push(`Not applied: ${payload.skipped.join(", ")}`);
  return bits.join(" · ");
}

function showAnswer(element, payload) {
  element.classList.add("plain");
  if (payload.route === "today") {
    element.innerHTML = `
      <article class="inbox-mail">
        <p class="mail-meta">From: analyst inbox · No warehouse query · No audit row</p>
        <p class="mail-body">${esc(payload.answer || "")}</p>
      </article>`;
    return;
  }
  const route = payload.route || "metric";
  const refused = route === "refuse";
  const applied = sliceLine(payload);
  const meta = [
    `<span class="route-badge ${esc(route)}">${esc(route)}</span>`,
    payload.metric ? `<span class="fine">Metric · ${esc(payload.metric)}</span>` : "",
    payload.engine ? `<span class="fine">${esc(payload.engine)}</span>` : "",
  ].filter(Boolean).join("");

  if (payload.metric === "call_list") {
    const calls = payload.rows || [];
    const dealRows = calls.flatMap((row) => (row.deals || []).map((deal) => [
      row.account_name,
      deal.family,
      deal.stage,
      deal.opened_date,
      money.format(deal.expected_net),
    ]));
    const callTable = calls.length
      ? table(
        ["Account", "Channel", "Subregion", "Open pipeline", "Win rate", "Why"],
        calls.map((row) => [row.account_name, row.channel, row.subregion, money.format(row.open_pipeline), pct(row.win_rate), row.reason])
      )
      : "";
    const dealTable = dealRows.length
      ? `<h3 style="margin-top:16px">Open deals</h3>${table(["Account", "Family", "Stage", "Opened", "Expected net"], dealRows)}`
      : "";
    element.innerHTML = `
      <article class="answer-card">
        <div class="answer-meta">${meta}</div>
        <p class="insight">${esc(payload.answer || "")}</p>
        ${applied ? `<p class="fine">${esc(applied)}</p>` : ""}
        ${callTable}
        ${dealTable}
        ${payload.sql ? `<pre class="sql-block">${esc(payload.sql)}</pre><p class="params">Params: ${esc(JSON.stringify(payload.params || []))}</p>` : ""}
      </article>`;
    return;
  }

  if (route === "plays") {
    const plays = (payload.rows || []).map((play) => `<article class="play"><h3>${esc(play.title)}</h3><p>${esc(play.detail)}</p></article>`).join("");
    const arenas = (payload.arenas || []).map((arena) => {
      const marks = (arena.marks || []).map((name) => brandMark(name)).join("");
      return `<article class="arena"><p class="kicker">${esc(arena.name)}</p><h3><span class="mark-slot">${marks}</span>${esc(arena.ours)}</h3><p>Against ${esc(arena.theirs)}.</p><p>${esc(arena.press)}</p></article>`;
    }).join("");
    element.innerHTML = `
      <article class="answer-card">
        <div class="answer-meta">${meta}</div>
        ${applied ? `<p class="fine">${esc(applied)}</p>` : ""}
        <div class="play-list">${plays}</div>
        <h3 style="margin-top:16px">Where the brands meet</h3>
        <div class="arena-grid">${arenas}</div>
      </article>`;
    return;
  }

  const sqlBlock = payload.sql
    ? `<pre class="sql-block">${esc(payload.sql)}</pre><p class="params">Params: ${esc(JSON.stringify(payload.params || []))}</p>`
    : refused
      ? `<p class="fine">No SQL. The refusal is audited and nothing is sent to Genie.</p>`
      : "";
  element.innerHTML = `
    <article class="answer-card${refused ? " refuse" : ""}">
      <div class="answer-meta">${meta}</div>
      <p class="insight">${esc(payload.answer || payload.error || "")}</p>
      ${applied ? `<p class="fine">${esc(applied)}</p>` : ""}
      ${rowsTable(payload.rows)}
      ${sqlBlock}
    </article>`;
}

function renderLabResult(payload) {
  const out = document.getElementById("lab-out");
  out.classList.add("plain");
  if (payload.kind === "board_brief") {
    const sections = (payload.sections || []).map((section) => `
      <article class="lab-section">
        <h4>${esc(section.metric)}</h4>
        <p class="fine">${esc(section.description || "")}</p>
        <p>${esc(section.insight || "")}</p>
        <p class="fine">${esc(section.row_count)} rows · ${esc(JSON.stringify(section.params || []))}</p>
      </article>`).join("");
    out.innerHTML = `
      <div class="lab-head"><span class="fine">Board brief · ${esc(payload.elapsed_ms)} ms</span></div>
      <p class="lab-narrative">${esc(payload.narrative || "")}</p>
      ${sections}`;
    return;
  }
  if (payload.kind === "eval_report") {
    const body = (payload.results || []).map((row) => `
      <tr>
        <td>${esc(row.id)}</td>
        <td>${esc(row.question)}</td>
        <td>${esc(row.expect)}${row.expect_metric ? ` / ${esc(row.expect_metric)}` : ""}</td>
        <td>${esc(row.got)}${row.got_metric ? ` / ${esc(row.got_metric)}` : ""}</td>
        <td class="${row.ok ? "ok" : "bad"}">${row.ok ? "pass" : "fail"}</td>
      </tr>`).join("");
    out.innerHTML = `
      <div class="lab-head">
        <span class="pass">${esc(payload.pass_pct)}% pass</span>
        <span class="fine">${esc(payload.passed)} / ${esc(payload.total)} · ${esc(payload.elapsed_ms)} ms</span>
        ${payload.failed ? `<span class="fail">${esc(payload.failed)} failed</span>` : ""}
      </div>
      <p class="fine">${esc(payload.note || "")}</p>
      <div class="row-table"><table class="eval-table"><thead><tr><th>Case</th><th>Question</th><th>Expect</th><th>Got</th><th></th></tr></thead><tbody>${body}</tbody></table></div>`;
    return;
  }
  if (payload.kind === "scope_pin") {
    out.innerHTML = `
      <div class="lab-head"><span class="fine">Scope pin · ${esc(payload.metric)}</span></div>
      <p class="fine">${esc(payload.note || "")}</p>
      <div class="scope-grid">
        <article class="scope-card"><span>Operator net sales</span><b>${esc(money.format(payload.operator_net_sales || 0))}</b><p class="fine">${esc(payload.operator_rows)} channel rows</p></article>
        <article class="scope-card"><span>Lakeshore Grocery</span><b>${esc(money.format(payload.lakeshore_net_sales || 0))}</b><p class="fine">${esc(payload.lakeshore_rows)} channel rows · ACCT-0001</p></article>
      </div>`;
    return;
  }
  out.textContent = JSON.stringify(payload, null, 2);
}

function setSlice(key, value) {
  slices[key] = value || "";
  document.querySelectorAll(`#slicers button[data-slice="${key}"]`).forEach((chip) => {
    chip.classList.toggle("on", chip.dataset.value === (value || ""));
  });
}

function clearSlices() {
  Object.keys(slices).forEach((key) => setSlice(key, ""));
}

function paintSubregions() {
  document.querySelectorAll("#slicers button[data-slice=subregion]").forEach((chip) => {
    const value = chip.dataset.value;
    const visible = !slices.region || !value || sliceTree[value] === slices.region;
    chip.hidden = !visible;
  });
  if (!slices.subregion) {
    const all = document.querySelector("#slicers button[data-slice=subregion][data-value='']");
    if (all) all.classList.add("on");
  }
}

function reloadAfterSlice() {
  paintSubregions();
  Object.keys(loaded).forEach((key) => {
    loaded[key] = false;
  });
  return show(currentTab);
}

const loaded = {};
let currentTab = "overview";
let renderGen = 0;

function current(gen) {
  return gen === renderGen;
}

async function show(tab) {
  const changed = tab !== currentTab;
  const gen = ++renderGen;
  currentTab = tab;
  if (changed) window.scrollTo(0, 0);
  document.getElementById("slicers").classList.toggle("idle", !slicedTabs.has(tab));
  document.querySelectorAll("nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tab);
  });
  document.querySelectorAll(".tab").forEach((section) => {
    section.hidden = section.id !== tab;
  });
  if (loaded[tab]) return;
  if (tab === "brief") await renderBrief(gen);
  if (tab === "overview") await renderOverview(gen);
  if (tab === "commercial") await renderCommercial(gen);
  if (tab === "analytics") await renderAnalytics(gen);
  if (tab === "supply") await renderSupply(gen);
  if (tab === "operations") await renderOperations(gen);
  if (tab === "market") await renderMarket(gen);
  if (tab === "assistant") await loadAudit(gen);
  if (tab === "lab") await renderLab(gen);
  if (tab === "catalog") await renderCatalog(gen);
  if (!current(gen)) return;
  loaded[tab] = true;
}

function warehouseStatus(warehouse) {
  const where = warehouse.catalog === "(workspace default)" ? warehouse.schema : `${warehouse.catalog}.${warehouse.schema}`;
  return `Reading ${where}`;
}

function showBackendNote(text) {
  const note = document.getElementById("dbx");
  note.hidden = !text;
  note.classList.remove("warn");
  note.textContent = text || "";
}

async function boot() {
  const session = await api("/api/session");
  if (!session.user) {
    location.href = "/login";
    return;
  }
  document.getElementById("who").textContent = `${session.user.label} · ${session.user.username}`;
  showBackendNote(session.lane_note || "");
  const options = await api("/api/slices");
  sliceTree = options.subregion_of || {};
  const groups = [
    ["channel", "Channel", options.channel || []],
    ["region", "Region", options.region || []],
    ["subregion", "Subregion", options.subregion || []],
    ["family", "Family", options.family || []],
    ["year", "Year", options.year || []],
  ];
  const slicer = document.getElementById("slicers");
  slicer.innerHTML = groups.map(([key, label, values]) => {
    const chips = [`<button type="button" data-slice="${key}" data-value="" class="on">All</button>`]
      .concat(values.map((value) => `<button type="button" data-slice="${key}" data-value="${esc(value)}">${esc(value)}</button>`));
    return `<div class="slice-group"><span>${esc(label)}</span>${chips.join("")}</div>`;
  }).join("") + `<p class="fine">Family filters invoices and opportunities. Activity has no brand, so activity counts stay on channel, region, subregion, and year.</p>`;
  slicer.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-slice]");
    if (!button) return;
    slices[button.dataset.slice] = button.dataset.value;
    if (button.dataset.slice === "region" && slices.subregion && sliceTree[slices.subregion] !== slices.region) {
      setSlice("subregion", "");
    }
    button.parentElement.querySelectorAll("button").forEach((item) => item.classList.toggle("on", item === button));
    reloadAfterSlice();
  });
  document.getElementById("chips").innerHTML = session.examples.map((example) => `<button type="button" data-example="${esc(example)}">${esc(example)}</button>`).join("");
  document.getElementById("chips").addEventListener("click", (event) => {
    const example = event.target.dataset.example;
    if (example) document.getElementById("q-next").value = example;
  });
  document.getElementById("demo-beats").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-beat]");
    if (!button) return;
    document.querySelectorAll("#demo-beats button").forEach((item) => item.classList.toggle("on", item === button));
    const beat = button.dataset.beat;
    const note = document.getElementById("voice-note");
    note.hidden = true;
    if (beat === "today") {
      clearSlices();
      document.getElementById("q-today").value = "trade spend by channel";
      await reloadAfterSlice();
      document.getElementById("ask-today").click();
      return;
    }
    if (beat === "margin") {
      clearSlices();
      document.getElementById("q-next").value = "margin by brand";
      await reloadAfterSlice();
      document.getElementById("ask-next").click();
      return;
    }
    if (beat === "club") {
      clearSlices();
      setSlice("channel", "Club");
      document.getElementById("q-next").value = "win rate";
      await reloadAfterSlice();
      document.getElementById("ask-next").click();
      return;
    }
    if (beat === "family") {
      clearSlices();
      setSlice("family", "Nerds");
      document.getElementById("q-next").value = "activity mix";
      await reloadAfterSlice();
      document.getElementById("ask-next").click();
      return;
    }
    if (beat === "nielsen") {
      clearSlices();
      document.getElementById("q-next").value = "what is our Nielsen share";
      await reloadAfterSlice();
      document.getElementById("ask-next").click();
      return;
    }
    if (beat === "ibp") {
      clearSlices();
      document.getElementById("q-next").value = "SAP IBP forecast for Nerds";
      await reloadAfterSlice();
      document.getElementById("ask-next").click();
    }
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
      body: JSON.stringify({ mode: "proposed", question: document.getElementById("q-next").value, ...sliceFields() }),
    });
    showAnswer(document.getElementById("out-next"), payload);
    document.getElementById("out-next").scrollIntoView({ block: "nearest", behavior: "smooth" });
    loaded.assistant = false;
    await loadAudit(undefined, true);
    loaded.assistant = true;
  });
  async function hear(body) {
    const response = await fetch("/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || "Voice is optional and is not configured on this host.");
    }
    const audio = new Audio(URL.createObjectURL(await response.blob()));
    await audio.play();
  }
  function renderCompare(payload, target) {
    const governed = payload.governed || {};
    const genie = payload.genie || {};
    const genieLines = genie.called
      ? [genie.answer || genie.error || "", genie.sql || "", genie.space_title ? `Space: ${genie.space_title}` : ""].filter(Boolean)
      : [genie.error || "Genie was not called."];
    const out = target || document.getElementById("lab-out");
    out.classList.add("plain");
    out.innerHTML = `<p class="compare-note">${esc(payload.note || "")}</p><div class="compare-grid"><article><h3>Governed</h3><p>${esc(governed.answer || "")}</p><p class="fine">${esc(governed.metric || governed.route || "")}</p></article><article><h3>Genie</h3><p>${esc(genieLines.join("\n\n"))}</p></article></div>`;
  }
  async function runLab(path, body) {
    const out = document.getElementById("lab-out");
    out.classList.remove("plain");
    out.classList.add("waiting");
    out.textContent = path.endsWith("/compare") ? "Asking the governed router and Genie…" : "Running…";
    const payload = await api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    out.classList.remove("waiting");
    if (payload.kind === "compare") {
      renderCompare(payload);
      return;
    }
    renderLabResult(payload);
  }
  document.getElementById("compete").addEventListener("click", async (event) => {
    if (event.target.id !== "ask-genie-compete") return;
    const box = document.getElementById("compete-genie");
    box.hidden = false;
    box.textContent = "Asking the governed router and Genie…";
    const payload = await api("/api/lab/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "show the public competitive set" }),
    });
    renderCompare(payload, box);
  });
  document.getElementById("run-board").addEventListener("click", () => runLab("/api/lab/board"));
  document.getElementById("hear-brief").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await hear({ source: "board" });
    } catch (error) {
      const out = document.getElementById("lab-out");
      out.classList.add("plain");
      out.innerHTML = `<p class="fine">${esc(error.message)}</p>`;
    } finally {
      button.disabled = false;
    }
  });
  document.getElementById("run-evals").addEventListener("click", () => runLab("/api/lab/evals"));
  document.getElementById("run-compare").addEventListener("click", () => {
    runLab("/api/lab/compare", { question: document.getElementById("genie-q").value });
  });
  document.getElementById("run-scope").addEventListener("click", () => runLab("/api/lab/scope", { metric: "net_by_channel" }));
  document.getElementById("hear").addEventListener("click", () => {
    const note = document.getElementById("voice-note");
    note.hidden = true;
    hear({ question: document.getElementById("q-next").value, ...sliceFields() }).catch((error) => {
      note.hidden = false;
      note.textContent = error.message;
    });
  });
  await show("brief");
}

boot().catch((error) => {
  if (error.message !== "auth") console.error(error);
});
