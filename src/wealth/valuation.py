"""Each source's raw records → holdings, valued at the market of the demo date.

One shape for every holding, whatever sent it::

    {"key", "owner", "source", "tier", "trust", "kind": "asset" | "liability", "class", "name",
     "value", "prev_value", "ytd_value", "cost", "liquid", "stress", "detail": {...}}

``value`` is today's value in VND, ``prev_value`` a month ago, ``ytd_value`` on 1 January (None
when unknown), ``cost`` what was paid (None when unknown). ``stress`` is the share of the value a
market stress shaves off (wealth.fixtures market ``stress_drawdown``). A liability's value is what
is owed, positive. ``detail`` also carries what the source knows of the purchase (``bought``,
``avg_price`` / ``avg_nav``, ``opened``, ``purchase_year``) for the holdings table.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from wealth.labels import SOURCES


def holding(
    owner: str,
    source: str,
    ident: str,
    *,
    trust: str,
    cls: str,
    name: str,
    value: float,
    prev_value: Optional[float] = None,
    ytd_value: Optional[float] = None,
    cost: Optional[float] = None,
    liquid: bool = False,
    stress: float = 0.0,
    kind: str = "asset",
    tier: Optional[int] = None,
    **detail: Any,
) -> Dict[str, Any]:
    return {
        "key": f"{owner}:{source}:{ident}",
        "owner": owner,
        "source": source,
        "tier": tier or SOURCES[source]["tier"],
        "trust": trust,
        "kind": kind,
        "class": cls,
        "name": name,
        "value": round(value),
        "prev_value": round(value if prev_value is None else prev_value),
        "ytd_value": None if ytd_value is None else round(ytd_value),
        "cost": None if cost is None else round(cost),
        "liquid": liquid,
        "stress": stress,
        "detail": detail,
    }


def stock(
    owner: str,
    source: str,
    row: Dict[str, Any],
    market: Dict[str, Any],
    trust: str,
    ident: Optional[str] = None,
    tier: Optional[int] = None,
) -> Dict[str, Any]:
    m = market["stocks"][row["ticker"]]
    qty = row["qty"]
    return holding(
        owner,
        source,
        ident or f"stock:{row['ticker']}",
        trust=trust,
        cls="stock",
        name=f"Cổ phiếu {row['ticker']}",
        value=qty * m["price"],
        prev_value=qty * m["prev_month"],
        ytd_value=qty * m["ytd_base"],
        cost=qty * row["avg_price"] if row.get("avg_price") else None,
        liquid=True,
        stress=round(market["stress_drawdown"]["stock_base"] * m["beta"], 4),
        tier=tier,
        ticker=row["ticker"],
        qty=qty,
        price=m["price"],
        avg_price=row.get("avg_price"),
        bought=row.get("bought"),
        sector=m["sector"],
        issuer=m["issuer"],
        beta=m["beta"],
    )


def bond(owner: str, source: str, row: Dict[str, Any], market: Dict[str, Any], trust: str) -> Dict[str, Any]:
    m = market["bonds"][row["code"]]
    qty = row["qty"]
    return holding(
        owner,
        source,
        f"bond:{row['code']}",
        trust=trust,
        cls="bond",
        name=f"Trái phiếu {row['code']} ({m['issuer']})",
        value=qty * m["price"],
        cost=qty * row["avg_price"] if row.get("avg_price") else None,
        liquid=m["kind"] == "government",
        stress=market["stress_drawdown"][f"bond_{m['kind']}"],
        code=row["code"],
        qty=qty,
        par=m["par"],
        price=m["price"],
        avg_price=row.get("avg_price"),
        bought=row.get("bought"),
        issuer=m["issuer"],
        sector=m["sector"],
        bond_kind=m["kind"],
        coupon=m["coupon"],
        coupon_months=m["coupon_months"],
        maturity=m["maturity"],
        duration=m["duration"],
    )


def techcombank(owner: str, raw: Dict[str, Any], market: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for a in raw.get("accounts", []):
        cls = "deposit" if a["type"] == "TD" else "cash"
        out.append(
            holding(
                owner,
                "techcombank",
                a["id"],
                trust="verified",
                cls=cls,
                name=a["name"],
                value=a["balance"],
                liquid=True,
                account_type=a["type"],
                rate=a.get("rate"),
                opened=a.get("opened"),
                maturity=a.get("maturity"),
            )
        )
    for c in raw.get("cards", []):
        if c.get("outstanding"):
            out.append(
                holding(
                    owner,
                    "techcombank",
                    c["id"],
                    trust="verified",
                    cls="card",
                    kind="liability",
                    name=f"Dư nợ thẻ {c['name']}",
                    value=c["outstanding"],
                    limit=c["limit"],
                )
            )
    for ln in raw.get("loans", []):
        out.append(
            holding(
                owner,
                "techcombank",
                ln["id"],
                trust="verified",
                cls="loan",
                kind="liability",
                name=ln["name"],
                value=ln["outstanding"],
                rate=ln["rate"],
                rate_type=ln["rate_type"],
                monthly_payment=ln["monthly_payment"],
                end=ln["end"],
                collateral=ln.get("collateral"),
            )
        )
    return out


def tcbs(owner: str, raw: Dict[str, Any], market: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = [stock(owner, "tcbs", s, market, "verified") for s in raw.get("stocks", [])]
    out += [bond(owner, "tcbs", b, market, "verified") for b in raw.get("bonds", [])]
    mg = raw.get("margin")
    if mg:
        out.append(
            holding(
                owner,
                "tcbs",
                mg["id"],
                trust="verified",
                cls="loan",
                kind="liability",
                name=mg["name"],
                value=mg["outstanding"],
                rate=mg["rate"],
                rate_type="floating",
                monthly_payment=0,
            )
        )
    return out


def techcom_capital(owner: str, raw: Dict[str, Any], market: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for f in raw.get("funds", []):
        m = market["funds"][f["code"]]
        u = f["units"]
        out.append(
            holding(
                owner,
                "techcom_capital",
                f"fund:{f['code']}",
                trust="verified",
                cls="fund",
                name=m["name"],
                value=u * m["nav"],
                prev_value=u * m["prev_month"],
                ytd_value=u * m["ytd_base"],
                cost=u * f["avg_nav"],
                liquid=m["liquid"],
                stress=m["drawdown"],
                code=f["code"],
                units=u,
                nav=m["nav"],
                avg_nav=f["avg_nav"],
                bought=f.get("bought"),
                fund_type=m["type"],
            )
        )
    return out


def property_value(row: Dict[str, Any], market: Dict[str, Any]) -> Dict[str, float]:
    area = market["areas"][row["area"]]
    return {"value": row["sqm"] * area["price_sqm"], "prev_value": row["sqm"] * area["prev_month"]}


def onehousing(owner: str, raw: Dict[str, Any], market: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for p in raw.get("properties", []):
        area = market["areas"][p["area"]]
        v = property_value(p, market)
        out.append(
            holding(
                owner,
                "onehousing",
                p["id"],
                trust="verified",
                cls="real_estate",
                name=p["name"],
                value=v["value"],
                prev_value=v["prev_value"],
                cost=p["purchase_price"],
                stress=market["stress_drawdown"]["real_estate"],
                area=p["area"],
                area_name=area["name"],
                city=area["city"],
                property_type=p["type"],
                sqm=p["sqm"],
                purchase_year=p["purchase_year"],
                rental_monthly=p.get("rental_monthly", 0),
                use=p.get("use"),
                months_to_sell=area["months_to_sell"],
            )
        )
    return out


def open_api(owner: str, raw: List[Dict[str, Any]], market: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Other banks and brokers the client let us read (Open API, NHNN's framework)."""
    out = []
    for inst in raw or []:
        if not inst.get("consent"):
            continue
        name = inst["institution"]
        for a in inst.get("accounts", []):
            out.append(
                holding(
                    owner,
                    "open_api",
                    f"{name}:{a['id']}",
                    trust="verified",
                    cls="cash",
                    name=a["name"],
                    value=a["balance"],
                    liquid=True,
                    institution=name,
                    account_type=a["type"],
                )
            )
        for s in inst.get("stocks", []):
            h = stock(owner, "open_api", s, market, "verified", ident=f"{name}:stock:{s['ticker']}")
            h["detail"]["institution"] = name
            h["name"] = f"{h['name']} ({name})"
            out.append(h)
    return out


def declared(owner: str, items: List[Dict[str, Any]], market: Dict[str, Any]) -> List[Dict[str, Any]]:
    """What the client says they hold. Gold and crypto are valued at market; a property in an
    area we know is valued by its area when it gives its size; the rest at the client's word."""
    sd = market["stress_drawdown"]
    out = []
    for d in items or []:
        cls = d["class"]
        ident = d.get("id") or d["name"]
        if cls == "gold":
            g = market["gold"]
            out.append(
                holding(
                    owner,
                    "declared",
                    ident,
                    trust="declared",
                    cls="gold",
                    name=d["name"],
                    value=d["qty"] * g["price_per_luong"],
                    prev_value=d["qty"] * g["prev_month"],
                    ytd_value=d["qty"] * g["ytd_base"],
                    liquid=True,
                    stress=sd["gold"],
                    qty=d["qty"],
                    unit="lượng",
                    price=g["price_per_luong"],
                )
            )
        elif cls == "crypto":
            c = market["crypto"][d["symbol"]]
            out.append(
                holding(
                    owner,
                    "declared",
                    ident,
                    trust="declared",
                    cls="crypto",
                    name=d["name"],
                    value=d["qty"] * c["price"],
                    prev_value=d["qty"] * c["prev_month"],
                    ytd_value=d["qty"] * c["ytd_base"],
                    liquid=True,
                    stress=sd["crypto"],
                    symbol=d["symbol"],
                    qty=d["qty"],
                )
            )
        elif cls == "real_estate":
            area = market["areas"].get(d.get("area") or "")
            if area and d.get("sqm"):
                value, prev = d["sqm"] * area["price_sqm"], d["sqm"] * area["prev_month"]
            else:
                value = prev = d.get("value") or 0
            out.append(
                holding(
                    owner,
                    "declared",
                    ident,
                    trust="declared",
                    cls="real_estate",
                    name=d["name"],
                    value=value,
                    prev_value=prev,
                    cost=d.get("purchase_price"),
                    stress=sd["real_estate"],
                    area=d.get("area"),
                    area_name=(area or {}).get("name") or d.get("location"),
                    city=(area or {}).get("city"),
                    sqm=d.get("sqm"),
                    purchase_year=d.get("purchase_year"),
                    rental_monthly=d.get("rental_monthly", 0),
                    months_to_sell=(area or {}).get("months_to_sell", 12),
                )
            )
        elif cls == "loan":
            out.append(
                holding(
                    owner,
                    "declared",
                    ident,
                    trust="declared",
                    cls="loan",
                    kind="liability",
                    name=d["name"],
                    value=d.get("value") or 0,
                    rate=d.get("rate"),
                    rate_type=d.get("rate_type", "fixed"),
                    monthly_payment=d.get("monthly_payment", 0),
                )
            )
        else:  # business, insurance, anything else: the client's own value
            out.append(
                holding(
                    owner,
                    "declared",
                    ident,
                    trust="declared",
                    cls=cls,
                    name=d["name"],
                    value=d.get("value") or 0,
                    stress=sd.get(cls, 0.0),
                    sector=d.get("sector"),
                    premium_annual=d.get("premium_annual"),
                    premium_month=d.get("premium_month"),
                )
            )
    return out
