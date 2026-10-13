"""The cash-flow calendar: what comes in and goes out, month by month.

Two kinds of items. **Recurring** ones are found in the account's transactions (a salary, a rent
received, school fees each quarter). **Product** ones come from what the client holds: a loan's
instalments, a card's balance (paid once, next month: what is owed today, not a bill every month),
a term deposit maturing, a bond's coupons, a stock's dividends, an insurance premium, and the dated
events the client told us about.
"""

from __future__ import annotations

import re
import statistics
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

TR = 1_000_000

# not recurring income or bills: day-to-day spending, and loan instalments and card payments (the
# loan and the card's balance themselves say)
SKIP = {"living", "loan", "card"}
LABELS = {
    "salary": "Lương",
    "pension": "Lương hưu",
    "rent": "Tiền thuê nhà nhận về",
    "card": "Thanh toán thẻ tín dụng",
    "school": "Học phí",
    "rent_out": "Tiền thuê nhà phải trả",
    "health": "Chi phí y tế",
}
# what the history calls the transactions the forecast leaves out
HISTORY_LABELS = {**LABELS, "living": "Chi tiêu sinh hoạt", "loan": "Trả nợ vay"}
HISTORY_MONTHS = 12


def month_add(ym: str, n: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    m0 = (m - 1) + n
    return f"{y + m0 // 12}-{m0 % 12 + 1:02d}"


def _norm(desc: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"T\d{1,2}/\d{4}|\d+", "", desc.upper())).strip()


def recurring(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Items seen in at least 3 months at a steady amount: monthly when they come almost every
    month, a few times a year (school terms, a quarterly bill) when they come every 2–4 months —
    then they recur in the same months of the year."""
    groups: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for t in transactions:
        if t.get("category") in SKIP:
            continue
        groups[(t.get("owner", ""), t["direction"], t.get("category", ""), _norm(t["desc"]))].append(t)
    out = []
    for (owner, direction, category, desc), rows in groups.items():
        months = sorted({r["date"][:7] for r in rows})
        if len(months) < 3:
            continue
        amounts = [r["amount"] for r in rows]
        med = statistics.median(amounts)
        if any(abs(a - med) > 0.35 * med for a in amounts):
            continue
        idx = [int(m[:4]) * 12 + int(m[5:7]) for m in months]
        gaps = [b - a for a, b in zip(idx, idx[1:])]
        if len(months) >= 9 and max(gaps) <= 2:
            cadence, when = "monthly", None
        elif len(months) <= 6 and all(g in (2, 3, 4) for g in gaps):  # school terms, a quarterly bill
            cadence, when = "quarterly", sorted({int(m[5:7]) for m in months})
        else:
            continue
        out.append(
            {
                "owner": owner,
                "direction": direction,
                "category": category,
                "label": LABELS.get(category, desc.title()),
                "desc": desc,
                "amount": round(med, -4),
                "cadence": cadence,
                "months": when,
                "seen": len(months),
            }
        )
    return sorted(out, key=lambda r: (r["direction"], -r["amount"]))


def build(
    holdings: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    as_of: str,
    months: int,
    big: float,
    market: Dict[str, Any],
) -> Dict[str, Any]:
    now = as_of[:7]
    start = month_add(now, 1)
    # this month is forecast with the rest; only the months after it are the calendar's ``months``
    horizon = [now] + [month_add(start, i) for i in range(months)]
    cal: Dict[str, List[Dict[str, Any]]] = {m: [] for m in horizon}

    def add(
        month: str,
        direction: str,
        amount: float,
        label: str,
        kind: str,
        owner: Optional[str] = None,
    ) -> None:
        if month in cal and amount:
            cal[month].append(
                {
                    "direction": direction,
                    "amount": round(amount),
                    "label": label,
                    "kind": kind,
                    "owner": owner,
                }
            )

    rec = recurring(transactions)
    renting = {r["owner"] for r in rec if r["category"] == "rent"}
    for r in rec:
        for m in horizon:
            if r["cadence"] == "monthly" or int(m[5:7]) in (r["months"] or []):
                add(m, r["direction"], r["amount"], r["label"], "recurring", r["owner"])

    for h in holdings:
        d, owner = h["detail"], h["owner"]
        if h["class"] == "loan" and d.get("monthly_payment"):
            end = (d.get("end") or "9999-12")[:7]
            for m in horizon:
                if m <= end:
                    add(m, "out", d["monthly_payment"], f"Trả nợ: {h['name']}", "loan", owner)
        elif h["class"] == "card" and h["value"]:
            add(start, "out", h["value"], f"Thanh toán dư nợ thẻ: {h['name'].removeprefix('Dư nợ thẻ ')}", "card", owner)
        elif h["class"] == "deposit" and d.get("maturity"):
            years = max(
                0.0,
                (date.fromisoformat(d["maturity"]) - date.fromisoformat(d.get("opened") or d["maturity"])).days / 365,
            )
            add(
                d["maturity"][:7],
                "in",
                h["value"] * (1 + (d.get("rate") or 0) * years),
                f"Đáo hạn: {h['name']}",
                "maturity",
                owner,
            )
        elif h["class"] == "bond":
            per = d["qty"] * d["par"] * d["coupon"] / max(1, len(d["coupon_months"]))
            for m in horizon:
                if int(m[5:7]) in d["coupon_months"] and m <= d["maturity"][:7]:
                    add(m, "in", per, f"Coupon {d['code']}", "coupon", owner)
            add(
                d["maturity"][:7],
                "in",
                d["qty"] * d["par"],
                f"Đáo hạn trái phiếu {d['code']}",
                "maturity",
                owner,
            )
        elif h["class"] == "stock" and d.get("ticker"):
            mk = market["stocks"][d["ticker"]]
            for m in horizon:
                if int(m[5:7]) in mk["div_months"] and mk["div"]:
                    add(m, "in", d["qty"] * mk["div"], f"Cổ tức {d['ticker']}", "dividend", owner)
        elif h["class"] == "real_estate" and d.get("rental_monthly") and owner not in renting:
            for m in horizon:
                add(m, "in", d["rental_monthly"], f"Cho thuê: {h['name']}", "rent", owner)
        elif h["class"] == "insurance" and d.get("premium_annual"):
            for m in horizon:
                if int(m[5:7]) == d.get("premium_month"):
                    add(
                        m,
                        "out",
                        d["premium_annual"],
                        f"Phí bảo hiểm: {h['name']}",
                        "insurance",
                        owner,
                    )

    for e in events:
        add(
            e["date"][:7],
            e["direction"],
            e["amount"],
            e["label"],
            e.get("category", "event"),
            e.get("owner"),
        )

    rows, large = [], []
    for m in horizon:
        rows.append(_month(m, cal[m]))
        if m != now:
            large += [{**i, "month": m} for i in cal[m] if i["direction"] == "out" and i["amount"] >= big]
    current, rows = rows[0], rows[1:]
    return {
        "start": start,
        "history": history(transactions, now),
        "current": current,
        "months": rows,
        "recurring": rec,
        "large": large,
        "total_in": sum(r["in"] for r in rows),
        "total_out": sum(r["out"] for r in rows),
    }


def _month(month: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    items = sorted(items, key=lambda i: (i["direction"], -i["amount"]))
    inflow = sum(i["amount"] for i in items if i["direction"] == "in")
    outflow = sum(i["amount"] for i in items if i["direction"] == "out")
    return {"month": month, "in": inflow, "out": outflow, "net": inflow - outflow, "items": items}


def history(transactions: List[Dict[str, Any]], now: str) -> List[Dict[str, Any]]:
    """The twelve months before ``now`` as they happened: every transaction, summed by what it was."""
    past = [month_add(now, -i) for i in range(HISTORY_MONTHS, 0, -1)]
    sums: Dict[str, Dict[Tuple[str, str], float]] = {m: defaultdict(float) for m in past}
    for t in transactions:
        m = t["date"][:7]
        if m in sums:
            cat = t.get("category", "")
            sums[m][(t["direction"], HISTORY_LABELS.get(cat, _norm(t["desc"]).title()))] += t["amount"]
    return [
        _month(m, [{"direction": d, "amount": round(a), "label": label, "kind": "actual", "owner": None}
                   for (d, label), a in sums[m].items()])
        for m in past
    ]
