"""Competitive briefing.

Public figures stay sourced and incomparable. Plays on the commercial book
come from approved metrics. Private peers keep a null revenue.
"""
from __future__ import annotations

from app.core import SliceError, clean_filters, run_metric

ROLES = (
    {
        "system": "SQLite",
        "job": "Sign-in, the audit log, and the curated public record. Also the book when Snowflake is not serving.",
    },
    {
        "system": "Snowflake",
        "job": "Serves the commercial Gold book: slicers, funnel, and the plays below.",
    },
    {
        "system": "Databricks",
        "job": "Genie discovery only. That space is not this book, and a refusal is not sent there.",
    },
)

GUESSES = (
    {
        "entity": "Mars Wrigley confectionery",
        "kind": "synthetic",
        "point": None,
        "low": 8,
        "high": 18,
        "unit": "USD billions",
        "method": (
            "Bloomberg reported on March 5, 2025 that a bond prospectus showed $54.6 billion of 2024 net sales for all of Mars, including pet care and food. "
            "No confectionery split was disclosed. This demo draws an illustrative $8–18 billion band for the candy overlap and does not pick a point. "
            "Not a filing, not Nielsen, and not a share."
        ),
    },
    {
        "entity": "Haribo",
        "kind": "synthetic",
        "point": 3.0,
        "low": 2.0,
        "high": 3.2,
        "unit": "EUR billions",
        "method": (
            "Haribo does not publish group revenue. Recent trade press clusters near €3 billion, a 2025 industry estimate cited near €3.2 billion, "
            "and an older published range of €1.7–2.0 billion. This demo’s best guess is €3.0 billion, the middle of the recent cluster. "
            "Not a filing and not Nielsen."
        ),
    },
    {
        "entity": "Perfetti Van Melle",
        "kind": "stated",
        "point": None,
        "low": 4.0,
        "high": None,
        "unit": "EUR billions, company floor",
        "method": (
            "Perfetti’s own site says 2025 net revenue sales were above €4 billion. "
            "No Airheads or Mentos split is published, so this demo does not invent one."
        ),
    },
)


ARENAS = (
    {
        "name": "Chewy fruit",
        "ours": "Nerds, SweeTarts",
        "theirs": "Mars Wrigley — Skittles, Starburst",
        "marks": ["Nerds", "SweeTarts"],
        "fact": "Ferrara’s FY2025 release says NERDS sales were up more than 9%, with no dollar figure. Mars’s filed cell stays empty. The candy band above is a synthetic guess on top of a whole-company prospectus figure.",
        "move": "Put Nerds and SweeTarts on that close.",
        "hold": "Do not turn the guess into a Skittles share.",
        "press": "Put Nerds and SweeTarts where this book already closes. Do not turn the guess into a Skittles share.",
    },
    {
        "name": "Gummy",
        "ours": "Trolli",
        "theirs": "Haribo — Goldbears",
        "marks": ["Trolli"],
        "fact": "Haribo publishes no group revenue. The figure above is a synthetic reconciliation of conflicting press estimates.",
        "move": "Take the gummy occasion in September and October on that close.",
        "hold": "",
        "press": "Take the gummy occasion in September and October on the accounts in this book.",
    },
    {
        "name": "Taffy",
        "ours": "Laffy Taffy",
        "theirs": "Perfetti Van Melle — Airheads, Mentos",
        "marks": ["Laffy Taffy"],
        "fact": "Perfetti states net revenue above €4 billion for 2025. No Airheads split is published, so none is guessed.",
        "move": "Win the taffy slot on that close.",
        "hold": "Airheads and Mentos stay a named overlap, not a dollar target.",
        "press": "Win the taffy slot in the channels with the higher close rate. Airheads and Mentos stay a named overlap, not a dollar target.",
    },
    {
        "name": "Bars",
        "ours": "Butterfinger, Baby Ruth",
        "marks": ["Butterfinger", "Baby Ruth"],
        "theirs": "Hershey confectionery",
        "fact": "Hershey’s 2025 consolidated net sales were $11,692.6 million. North America Confectionery was $9,479.7 million of that. That is not a sugar-only base.",
        "move": "Take the bar occasions on that close.",
        "hold": "Do not try to out-scale Hershey’s consolidated company.",
        "press": "Do not try to out-scale Hershey’s consolidated company. Take the bar occasions inside these accounts.",
    },
    {
        "name": "Seasonal sugar",
        "ours": "Brach's, Lemonhead",
        "marks": ["Brach's", "Lemonhead"],
        "theirs": "Seasonal displays, including the peers above",
        "fact": "Ferrara’s FY2025 release is $2.2 billion net sales, up 3.8%. A 2023 sugar share of 20.1% was not restated for 2025.",
        "move": "The display fight is on that close.",
        "hold": "Use the 2025 release. Leave the 2023 share in its year. This is not a syndicated rank.",
        "press": "Use the 2025 release. Leave the 2023 share in its year. Seasonal sugar here is a display fight, not a syndicated rank.",
    },
)


def compete_brief(book, public, account_id=None, filters=None):
    chosen = clean_filters(filters)
    landscape = run_metric(public, "public_landscape")
    families = _rows(book, "net_by_family", account_id, chosen)
    wins = _rows(book, "win_rate_by_channel", account_id, chosen)
    regions = _rows(book, "win_rate_by_region", account_id, chosen)
    subregions = _rows(book, "win_rate_by_subregion", account_id, chosen)
    years = _rows(book, "net_by_year", account_id, chosen)
    trade = _rows(book, "trade_by_channel", account_id, chosen)
    halloween = _rows(book, "halloween_window", account_id, chosen)
    scope = ""
    if chosen:
        scope = " Slice: " + ", ".join(f"{key} {value}" for key, value in chosen.items()) + "."
    return {
        "kind": "compete",
        "book_label": (
            "These plays use this synthetic book, seven fiscal years and four regions"
            + (f", for account {account_id}" if account_id else "")
            + "."
            + scope
            + " They are not Ferrara results and not a competitor’s P&L."
        ),
        "filters": chosen,
        "boundary": (
            "A current Nielsen, Circana, or NIQ share is still refused. "
            "The 20.1% figure is a 2023 company claim."
        ),
        "roles": list(ROLES),
        "scale": _scale(landscape),
        "private": _private(landscape),
        "guesses": list(GUESSES),
        "arenas": _placed_arenas(wins, subregions),
        "plays": _plays(wins, trade, halloween, families, regions, subregions, years, bool(chosen)),
    }


def _rows(conn, name, account_id, filters):
    try:
        return run_metric(conn, name, account_id, filters)
    except SliceError:
        raise
    except Exception:
        return []


def _scale(rows):
    wanted = {
        ("Ferrara Candy Company", "Net sales"),
        ("The Hershey Company", "Consolidated net sales"),
        ("Mondelēz International", "Net revenues"),
        ("Tootsie Roll Industries", "Net product sales"),
        ("CTH Invest Group", "Consolidated revenue"),
        ("3F's Holding", "Consolidated revenue"),
    }
    picked = [
        {
            "entity": row["entity"],
            "metric": row["metric"],
            "value_num": row["value_num"],
            "unit": row["unit"],
            "period": row["period"],
            "scope_note": row["scope_note"],
        }
        for row in rows
        if (row["entity"], row["metric"]) in wanted and row["value_num"] is not None
    ]
    return picked


def _private(rows):
    return [
        {"entity": row["entity"], "scope_note": row["scope_note"], "value_num": row["value_num"]}
        for row in rows
        if row["group_name"] == "Private peer"
    ]


def _close_place(wins, subregions):
    channels = [row for row in wins if row.get("win_rate") is not None and row.get("opportunities")]
    if not channels:
        return ""
    strong = max(channels, key=lambda row: (row["win_rate"], row["opportunities"]))
    line = (
        f"{strong['channel']} already wins {strong['win_rate']}% "
        f"({int(strong['won'])} of {int(strong['opportunities'])})."
    )
    places = [row for row in subregions if row.get("win_rate") is not None and row.get("opportunities")]
    if len(places) >= 2:
        best = max(places, key=lambda row: (row["win_rate"], row["opportunities"]))
        line += f" {best['subregion']} is the strongest subregion in view at {best['win_rate']}%."
    elif len(places) == 1:
        only = places[0]
        line += f" {only['subregion']} is the subregion in view, at {only['win_rate']}%."
    return line


def _placed_arenas(wins, subregions):
    place = _close_place(wins, subregions)
    placed = []
    for arena in ARENAS:
        copy = {key: value for key, value in arena.items() if key not in ("move", "hold")}
        if place:
            copy["press"] = " ".join(part for part in (place, arena["move"], arena["hold"]) if part)
        placed.append(copy)
    return placed


def _plays(wins, trade, halloween, families, regions, subregions, years, scoped=False):
    usable = [row for row in wins if row.get("win_rate") is not None]
    if not usable:
        return [
            {
                "title": "No opportunity gold on the serving warehouse",
                "detail": "Channel plays stay off until the book is loaded. The public record still stands, and private peers still have no estimated revenue.",
            }
        ]
    ranked = sorted(usable, key=lambda row: row["win_rate"])
    weak, strong = ranked[0], ranked[-1]
    trade_by = {row["channel"]: row for row in trade}
    weak_trade = trade_by.get(weak["channel"])
    plays = [
        {
            "title": f"Stop paying for misses in {weak['channel']}",
            "detail": (
                f"{weak['channel']} wins {weak['win_rate']}% of opportunities "
                f"({int(weak['won'])} of {int(weak['opportunities'])}). "
                + (
                    f"Trade there is {weak_trade['trade_pct']}% of gross. "
                    if weak_trade and weak_trade.get("trade_pct") is not None
                    else ""
                )
                + "Fix the close before adding distribution or trade."
            ),
        },
        {
            "title": f"Load the season into {strong['channel']}",
            "detail": (
                f"{strong['channel']} already wins {strong['win_rate']}% "
                f"({int(strong['won'])} of {int(strong['opportunities'])}). "
                "That is where a Halloween display has a book to land in."
            ),
        },
    ]
    if weak["channel"] == strong["channel"]:
        plays = plays[:1]
    plays.extend(_geo_plays(regions, "region"))
    plays.extend(_geo_plays(subregions, "subregion"))
    plays.extend(_year_play(years, scoped))
    window = next((row for row in halloween if row.get("season_window") == "Halloween window"), None)
    rest = next((row for row in halloween if row.get("season_window") == "Rest of book"), None)
    if window and rest and window.get("net_sales") is not None and rest.get("net_sales") is not None:
        plays.append(
            {
                "title": "Own September and October on four families",
                "detail": (
                    f"The Halloween window is ${window['net_sales']:,.0f} net on Nerds, Trolli, SweeTarts, and Laffy Taffy. "
                    f"The rest of this book is ${rest['net_sales']:,.0f}. "
                    "Ferrara’s FY2025 release says NERDS was up more than 9%, with no dollar figure. "
                    "Press that occasion. Do not turn 9% into a sales claim, and do not turn it into Haribo’s or Mars’s sales."
                ),
            }
        )
    if families and families[0].get("net_sales") is not None:
        top = families[0]
        plays.append(
            {
                "title": f"This slice is already heavy in {top['family']}",
                "detail": (
                    f"{top['family']} is ${top['net_sales']:,.0f} net inside this synthetic book. "
                    "That is where these accounts are concentrated. It is not a national rank."
                ),
            }
        )
    plays.extend(_trade_miss(usable, trade, weak["channel"]))
    plays.append(
        {
            "title": "Do not fight the wrong denominator",
            "detail": (
                "Hershey’s 2025 consolidated net sales are $11,692.6 million, of which North America Confectionery is $9,479.7 million. "
                "Mondelēz 2025 net revenues are $38,537 million of global snacking. "
                "Ferrara’s own FY2025 release is $2.2 billion. Tootsie Roll’s 2025 product sales are $724.7 million. "
                "CTH Invest is €3.25 billion and includes more than Ferrara. 3F’s Holding is €22.3 billion and is not Ferrara. "
                "Filed rows for Mars, Haribo, and Perfetti still have no revenue. A labeled synthetic guess is a different panel."
            ),
        }
    )
    plays.append(
        {
            "title": "Five public brands are outside this book",
            "detail": "Jelly Belly, Black Forest, Dori, Carambar, and Spree are on the Ferrara site and are not families in this warehouse. These plays cannot steer them.",
        }
    )
    return plays


def _geo_plays(rows, key):
    usable = [row for row in rows if row.get("win_rate") is not None and row.get("opportunities")]
    if len(usable) < 2:
        return []
    ranked = sorted(usable, key=lambda row: (row["win_rate"], -row["opportunities"]))
    weak, strong = ranked[0], ranked[-1]
    place = "region" if key == "region" else "subregion"
    return [
        {
            "title": f"Fix the close in {weak[key]}",
            "detail": (
                f"{weak[key]} wins {weak['win_rate']}% of opportunities "
                f"({int(weak['won'])} of {int(weak['opportunities'])}). "
                f"{strong[key]} already wins {strong['win_rate']}% "
                f"({int(strong['won'])} of {int(strong['opportunities'])}). "
                f"Repair the {place} that misses before adding distribution there."
            ),
        }
    ]


def _year_play(years, scoped=False):
    usable = [row for row in years if row.get("net_sales") is not None]
    if len(usable) < 2:
        return []
    first, last = usable[0], usable[-1]
    where = "slice" if scoped else "book"
    return [
        {
            "title": f"{last['year']} is the largest year in this {where}",
            "detail": (
                f"{first['year']} net is ${first['net_sales']:,.0f}. {last['year']} net is ${last['net_sales']:,.0f}. "
                "The later years are larger because the generator steps the book up. "
                "That step is not Ferrara’s reported 3.8%."
            ),
        }
    ]


def _trade_miss(wins, trade, weak_channel):
    win_map = {row["channel"]: row["win_rate"] for row in wins}
    rates = sorted(row["trade_pct"] for row in trade if row.get("trade_pct") is not None)
    win_rates = sorted(row["win_rate"] for row in wins if row.get("win_rate") is not None)
    if not rates or not win_rates:
        return []
    trade_mid = rates[len(rates) // 2]
    win_mid = win_rates[len(win_rates) // 2]
    for row in trade:
        win = win_map.get(row["channel"])
        if win is None or row.get("trade_pct") is None:
            continue
        if row["channel"] == weak_channel:
            continue
        if row["trade_pct"] >= trade_mid and win <= win_mid:
            return [
                {
                    "title": f"Trade in {row['channel']} is not buying the close",
                    "detail": (
                        f"Trade is {row['trade_pct']}% of gross and the win rate is {win}%. "
                        "Spend that follows a loss is not a weapon."
                    ),
                }
            ]
    return []
