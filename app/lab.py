"""Interview lab: board brief, golden evals, scope pin, Genie compare, 90-day plan.

Adapted from the Visual Comfort lab shape. Numbers come from this demo's
approved metrics. Genie is not simulated.
"""
from __future__ import annotations

import time

from app.core import METRICS, answer, insight, metric_sql, run_metric
from app.databricks_backend import genie_status

BOARD_CHAIN = (
    "commercial_funnel",
    "trade_by_channel",
    "win_rate_by_channel",
    "margin_by_family",
    "net_by_month",
)

EVAL_CASES = [
    {"id": "funnel", "lane": "metric", "question": "show the commercial funnel", "expect": "metric", "metric": "commercial_funnel"},
    {"id": "pipeline", "lane": "metric", "question": "open pipeline", "expect": "metric", "metric": "pipeline_by_stage"},
    {"id": "win", "lane": "metric", "question": "win rate by channel", "expect": "metric", "metric": "win_rate_by_channel"},
    {"id": "trade", "lane": "metric", "question": "trade spend by channel", "expect": "metric", "metric": "trade_by_channel"},
    {"id": "margin", "lane": "metric", "question": "margin by brand", "expect": "metric", "metric": "margin_by_family"},
    {"id": "season", "lane": "metric", "question": "halloween season", "expect": "metric", "metric": "net_by_month"},
    {"id": "channel", "lane": "metric", "question": "net sales by channel", "expect": "metric", "metric": "net_by_channel"},
    {"id": "peers", "lane": "metric", "question": "show the public competitive set", "expect": "metric", "metric": "public_landscape"},
    {"id": "nielsen", "lane": "refuse", "question": "what is our Nielsen share", "expect": "refuse"},
    {"id": "ibp", "lane": "refuse", "question": "SAP IBP forecast for Nerds", "expect": "refuse"},
    {"id": "mdm", "lane": "refuse", "question": "do we own enterprise MDM", "expect": "refuse"},
    {"id": "empty", "lane": "refuse", "question": "   ", "expect": "refuse"},
]

PLAN_90 = {
    "title": "What I would put in place in 90 days",
    "subtitle": "A Ferrara-flavored commercial analytics plan. Not a commitment, and not a description of their stack.",
    "phases": [
        {
            "days": "Days 1–30",
            "theme": "One commercial definition",
            "bullets": [
                "Write the activity, opportunity, invoice, trade, and gross-margin definitions the business will accept.",
                "Land them as Gold metrics with a quarantine gate, the way this book keeps four bad invoices out.",
                "Put published company figures in a separate context table. Do not mix them into customer net sales.",
                "Stand up the approved-metric router and a golden set before any model is allowed to say a number.",
            ],
        },
        {
            "days": "Days 31–60",
            "theme": "Measure the router",
            "bullets": [
                "Run the golden set in CI: right metric, refusal on syndicated share and demand-planning forecasts, audit row every time.",
                "Pin an account session and prove the same question returns a smaller book.",
                "If Databricks is the platform, publish the same Gold tables and keep the metric SQL identical.",
                "Use Genie or an equivalent only as a discovery lane. Promote a question into the registry after it passes the eval.",
            ],
        },
        {
            "days": "Days 61–90",
            "theme": "Hand it to the business",
            "bullets": [
                "Shadow the router against the analyst inbox on warehouse questions only.",
                "Publish a conflict log when two public sources disagree, as the workforce figures do.",
                "Write the runbook for adding a metric and for retiring a bad generated query.",
                "Leave SAP IBP, syndicated measurement, and MDM as explicit non-goals until the source system exists.",
            ],
        },
    ],
    "non_goals": [
        "Not a claim that Ferrara runs Databricks, Genie, or this warehouse.",
        "Not a current Nielsen, Circana, or NIQ share.",
        "Not an SAP IBP forecast and not an MDM program.",
    ],
}


def board_brief(conn, account_id=None):
    started = time.perf_counter()
    sections = []
    for name in BOARD_CHAIN:
        sql, params = metric_sql(name, account_id)
        rows = run_metric(conn, name, account_id)
        sections.append(
            {
                "metric": name,
                "description": METRICS[name]["description"],
                "insight": insight(name, rows),
                "sql": " ".join(sql.split()),
                "params": list(params),
                "rows": rows[:8],
                "row_count": len(rows),
            }
        )
    narrative = " ".join(section["insight"] for section in sections)
    narrative += " The public competitive set is a different table and is not part of this book."
    return {
        "kind": "board_brief",
        "narrative": narrative,
        "sections": sections,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
    }


def run_evals(conn, username="lab", account_id=None, audit_conn=None):
    started = time.perf_counter()
    results = []
    for case in EVAL_CASES:
        t0 = time.perf_counter()
        payload = answer(conn, case["question"], username, account_id, audit_conn=audit_conn)
        ok = payload["route"] == case["expect"] and (
            case["expect"] != "metric" or payload["metric"] == case["metric"]
        )
        results.append(
            {
                "id": case["id"],
                "lane": case["lane"],
                "question": case["question"].strip() or "(empty)",
                "expect": case["expect"],
                "expect_metric": case.get("metric"),
                "got": payload["route"],
                "got_metric": payload["metric"],
                "ok": ok,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
            }
        )
    passed = sum(1 for row in results if row["ok"])
    return {
        "kind": "eval_report",
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_pct": round(100.0 * passed / len(results), 1) if results else 0,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "note": "Golden prompts for the approved-metric router. Not a language-model eval.",
        "results": results,
    }


def compare(conn, question, username, account_id=None, audit_conn=None):
    governed = answer(conn, question, username, account_id, audit_conn=audit_conn)
    genie = genie_status()
    if governed["route"] == "metric":
        note = "The governed router answered from an approved metric. Genie is not called."
    else:
        note = "The governed router refused. A discovery model is not allowed to fill that gap in this demo."
    return {"kind": "compare", "question": question, "governed": governed, "genie": genie, "note": note}


def scope_pin(conn, metric="net_by_channel"):
    full = run_metric(conn, metric, None)
    scoped = run_metric(conn, metric, "ACCT-0001")
    full_net = round(sum(row.get("net_sales") or 0 for row in full), 2)
    scoped_net = round(sum(row.get("net_sales") or 0 for row in scoped), 2)
    return {
        "kind": "scope_pin",
        "metric": metric,
        "operator_net_sales": full_net,
        "lakeshore_net_sales": scoped_net,
        "operator_rows": len(full),
        "lakeshore_rows": len(scoped),
        "note": "Same metric SQL. The account session binds ACCT-0001.",
    }


def plan():
    return {"kind": "plan_90", **PLAN_90}
