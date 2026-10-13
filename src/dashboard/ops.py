"""Each section of the dashboard is one op over the consolidated holdings.

Net worth, allocation, profit and loss against the client's benchmark, the drawdown threshold
against an estimate of today's, concentration, the liquidity reserve in months of spending, and
the cash-flow calendar. ``assemble`` puts them on one page.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from operonx import op

from dashboard import _calendar
from wealth import fixtures, profile
from wealth.labels import CLASSES, GROUPS, TRUST, TRUST_WEIGHT
from wealth.money import TR, months_text, pct, vnd

INVESTED = ("stock", "fund", "bond")
LIQUID = ("cash", "deposit")


def _assets(holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [h for h in holdings if h["kind"] == "asset"]


@op
def check_request(client_id: str = None, scope: str = None, months: int = None) -> dict:
    """What a caller sent, checked: a known client, a scope, 1–36 months."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    return {
        "client_id": client_id,
        "scope": scope or "personal",
        "months": max(1, min(36, int(months or 12))),
    }


@op
def client_profile(client_id: str, members: list) -> dict:
    """What the numbers are measured against: income, spending, the benchmark, the drawdown the
    client accepts (from their last risk test, else their file), dependents and dated events —
    summed over the household's members in the family view."""
    return {"profile": profile.build(client_id, members)}


@op
def net_worth(holdings: list) -> dict:
    """Assets less what is owed, its change over the month, and how much of it is verified."""
    assets = sum(h["value"] for h in _assets(holdings))
    debt = sum(h["value"] for h in holdings if h["kind"] == "liability")
    prev_assets = sum(h["prev_value"] for h in _assets(holdings))
    nw, prev = assets - debt, prev_assets - debt
    mix: Dict[str, float] = defaultdict(float)
    for h in _assets(holdings):
        mix[h["trust"]] += h["value"]
    confidence = sum(TRUST_WEIGHT[t] * v for t, v in mix.items()) / assets if assets else 0.0
    return {
        "net_worth": {
            "value": nw,
            "assets": assets,
            "liabilities": debt,
            "prev_value": prev,
            "month_change": nw - prev,
            "month_change_pct": (nw - prev) / prev if prev else 0.0,
            "trust_mix": [
                {"trust": t, "label": TRUST[t], "value": v, "share": v / assets if assets else 0}
                for t, v in sorted(mix.items(), key=lambda kv: -kv[1])
            ],
            "confidence": round(confidence, 3),
        }
    }


@op
def allocation(holdings: list) -> dict:
    """Assets by group, largest first, each with its profit against what was paid (over the
    holdings whose cost is known; ``pnl`` is None when no holding of the group has one)."""
    groups: Dict[str, float] = defaultdict(float)
    marked: Dict[str, float] = defaultdict(float)
    paid: Dict[str, float] = defaultdict(float)
    for h in _assets(holdings):
        g = GROUPS.get(h["class"], CLASSES.get(h["class"], h["class"]))
        groups[g] += h["value"]
        if h["cost"] is not None:
            marked[g] += h["value"]
            paid[g] += h["cost"]
    total = sum(groups.values())
    return {
        "allocation": [
            {
                "group": g,
                "value": v,
                "share": v / total if total else 0,
                "pnl": marked[g] - paid[g] if g in paid else None,
                "return": (marked[g] - paid[g]) / paid[g] if paid.get(g) else None,
            }
            for g, v in sorted(groups.items(), key=lambda kv: -kv[1])
        ]
    }


@op
def performance(holdings: list, realized_ytd: int, profile: dict) -> dict:
    """The investments' profit: taken (this year) and on paper, and this year's return against
    the client's benchmark."""
    mk = fixtures.market()
    inv = [h for h in _assets(holdings) if h["class"] in INVESTED]
    unrealized = sum(h["value"] - h["cost"] for h in inv if h["cost"] is not None)
    cost = sum(h["cost"] for h in inv if h["cost"] is not None)
    marked = [h for h in _assets(holdings) if h["ytd_value"]]
    base = sum(h["ytd_value"] for h in marked)
    ytd = (sum(h["value"] for h in marked) - base) / base if base else 0.0
    bench = mk["benchmarks"].get(profile["benchmark"]) or mk["benchmarks"]["VNINDEX"]
    by_class = []
    for cls in INVESTED:
        rows = [h for h in inv if h["class"] == cls and h["cost"] is not None]
        if rows:
            v, c = sum(h["value"] for h in rows), sum(h["cost"] for h in rows)
            by_class.append(
                {
                    "class": cls,
                    "label": CLASSES[cls],
                    "value": v,
                    "cost": c,
                    "pnl": v - c,
                    "return": (v - c) / c if c else 0,
                }
            )
    return {
        "performance": {
            "realized_ytd": realized_ytd,
            "unrealized": unrealized,
            "invested_cost": cost,
            "unrealized_pct": unrealized / cost if cost else 0.0,
            "ytd_return": ytd,
            "benchmark": profile["benchmark"],
            "benchmark_name": bench["name"],
            "benchmark_ytd": bench["ytd"],
            "vs_benchmark": ytd - bench["ytd"],
            "by_class": by_class,
        }
    }


@op
def drawdown(holdings: list, net_worth: dict, profile: dict) -> dict:
    """What a market stress would take off the net worth today (each holding's own stress
    factor), against the most the client accepts."""
    nw = net_worth["value"]
    loss = sum(h["value"] * h["stress"] for h in _assets(holdings))
    current = loss / nw if nw > 0 else 0.0
    limit = profile["drawdown_limit"]
    status = "ok" if current <= 0.8 * limit else "near" if current <= limit else "over"
    top = sorted(_assets(holdings), key=lambda h: -h["value"] * h["stress"])[:4]
    return {
        "risk": {
            "limit": limit,
            "current": round(current, 4),
            "stress_loss": round(loss),
            "status": status,
            "top": [
                {"name": h["name"], "loss": round(h["value"] * h["stress"]), "stress": h["stress"]}
                for h in top
                if h["stress"]
            ],
        }
    }


@op
def concentration(holdings: list, net_worth: dict) -> dict:
    """Where too much sits in one place: one area, one issuer, one sector, one holding."""
    assets = net_worth["assets"] or 1
    areas: Dict[str, float] = defaultdict(float)
    issuers: Dict[str, float] = defaultdict(float)
    sectors: Dict[str, float] = defaultdict(float)
    for h in _assets(holdings):
        d = h["detail"]
        if h["class"] == "real_estate":
            areas[d.get("area_name") or h["name"]] += h["value"]
        if h["class"] in ("stock", "bond"):
            issuers[d.get("issuer") or h["name"]] += h["value"]
        if h["class"] in ("stock", "bond", "business") and d.get("sector"):
            sectors[d["sector"]] += h["value"]
    rows, warnings = [], []
    for kind, label, bucket, limit in (
        ("area", "Khu vực BĐS", areas, 0.35),
        ("issuer", "Tổ chức phát hành", issuers, 0.10),
        ("sector", "Ngành", sectors, 0.20),
    ):
        for name, v in sorted(bucket.items(), key=lambda kv: -kv[1]):
            share = v / assets
            flag = share > limit
            rows.append(
                {
                    "kind": kind,
                    "kind_label": label,
                    "name": name,
                    "value": v,
                    "share": share,
                    "limit": limit,
                    "flag": flag,
                }
            )
            if flag:
                warnings.append(f"{label} {name}: {pct(share)} tài sản (ngưỡng {pct(limit, digits=0)})")
    return {"concentration": {"rows": rows, "warnings": warnings}}


@op
def liquidity(holdings: list, profile: dict) -> dict:
    """Money that can be had within days — cash, deposits, money-market and bond funds,
    government bonds — as months of the client's spending."""
    keep = [
        h
        for h in _assets(holdings)
        if h["class"] in LIQUID
        or (h["class"] == "fund" and h["liquid"])
        or (h["class"] == "bond" and h["detail"].get("bond_kind") == "government")
    ]
    liquid = sum(h["value"] for h in keep)
    spend = profile["spending_monthly"] or 1
    months = liquid / spend
    status = "ok" if months >= 6 else "low" if months >= 3 else "critical"
    return {
        "liquidity": {
            "value": liquid,
            "spending_monthly": profile["spending_monthly"],
            "months": round(months, 1),
            "status": status,
            "items": [{"name": h["name"], "value": h["value"]} for h in keep],
        }
    }


@op
def cashflow(holdings: list, transactions: list, profile: dict, months: int = 12) -> dict:
    """The next months' money in and out (see dashboard/_calendar.py), and the large payments."""
    mk = fixtures.market()
    big = max(500 * TR, 3 * profile["spending_monthly"])
    return {"cashflow": _calendar.build(holdings, transactions, profile["events"], mk["as_of"], months, big, mk)}


@op
def assemble(
    client_id: str,
    scope: str,
    members: list,
    waiting: list,
    sources: list,
    holdings: list,
    profile: dict,
    net_worth: dict,
    allocation: list,
    performance: dict,
    risk: dict,
    concentration: dict,
    liquidity: dict,
    cashflow: dict,
) -> dict:
    """The page: every section, and the headline lines a reader sees first."""
    mk = fixtures.market()
    headline = {
        "net_worth": vnd(net_worth["value"]),
        "month_change": pct(net_worth["month_change_pct"], signed=True),
        "allocation": " · ".join(f"{a['group']} {pct(a['share'], digits=0)}" for a in allocation[:4]),
        "liquidity": f"{vnd(liquidity['value'])} = đủ chi {months_text(liquidity['months'])}",
        "risk": f"Ngưỡng {pct(risk['limit'], digits=0)} · hiện tại {pct(risk['current'])}",
    }
    return {
        "dashboard": {
            "client_id": client_id,
            "scope": scope,
            "as_of": mk["as_of"],
            "members": members,
            "waiting": waiting,
            "profile": profile,
            "sources": sources,
            "holdings": holdings,
            "net_worth": net_worth,
            "allocation": allocation,
            "performance": performance,
            "risk": risk,
            "concentration": concentration,
            "liquidity": liquidity,
            "cashflow": cashflow,
            "headline": headline,
        }
    }
