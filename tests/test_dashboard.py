import asyncio

from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient

from dashboard import _calendar
from dashboard.graph import dashboard_flow
from dashboard.ops import concentration, drawdown, liquidity, net_worth
from wealth import fixtures
from wealth.money import TR, TY

ENGINE = Operon(dashboard_flow, params={"client_id": None, "scope": None, "months": None})


def h(cls, value, kind="asset", trust="verified", prev=None, stress=0.0, liquid=False, **detail):
    return {
        "key": f"x:{cls}:{value}",
        "owner": "C01",
        "source": "techcombank",
        "tier": 1,
        "trust": trust,
        "kind": kind,
        "class": cls,
        "name": cls,
        "value": value,
        "prev_value": prev or value,
        "ytd_value": None,
        "cost": None,
        "liquid": liquid,
        "stress": stress,
        "detail": detail,
    }


def test_net_worth_is_assets_less_debt_with_its_month_change_and_confidence():
    rows = [
        h("deposit", 6 * TY),
        h("gold", 4 * TY, trust="declared", prev=3 * TY),
        h("loan", 2 * TY, kind="liability"),
    ]
    nw = net_worth(holdings=rows)()["net_worth"]
    assert (nw["value"], nw["prev_value"]) == (8 * TY, 7 * TY)
    assert round(nw["month_change_pct"], 4) == round(1 / 7, 4)
    assert nw["confidence"] == round((6 + 0.6 * 4) / 10, 3)


def test_drawdown_compares_a_stress_with_the_limit():
    rows = [h("stock", 10 * TY, stress=0.3), h("deposit", 10 * TY)]
    risk = drawdown(holdings=rows, net_worth={"value": 20 * TY}, profile={"drawdown_limit": 0.10})()["risk"]
    assert (risk["current"], risk["status"]) == (0.15, "over")
    calm = drawdown(holdings=rows, net_worth={"value": 20 * TY}, profile={"drawdown_limit": 0.30})()["risk"]
    assert calm["status"] == "ok"


def test_concentration_flags_one_area_over_its_share():
    rows = [h("real_estate", 8 * TY, area_name="Thảo Điền"), h("deposit", 2 * TY)]
    out = concentration(holdings=rows, net_worth={"assets": 10 * TY})()["concentration"]
    assert out["warnings"] == ["Khu vực BĐS Thảo Điền: 80% tài sản (ngưỡng 35%)"]


def test_liquidity_counts_cash_deposits_and_liquid_funds_not_stocks():
    rows = [
        h("deposit", 1 * TY),
        h("fund", 500 * TR, liquid=True),
        h("fund", 900 * TR),
        h("stock", 5 * TY, liquid=True),
    ]
    out = liquidity(holdings=rows, profile={"spending_monthly": 100 * TR})()["liquidity"]
    assert (out["value"], out["months"], out["status"]) == (1_500 * TR, 15.0, "ok")


def test_recurring_items_are_found_monthly_and_by_school_term():
    tx = [
        {
            "date": f"2026-{m:02d}-05",
            "amount": 120 * TR,
            "direction": "in",
            "desc": f"LUONG T{m}/2026",
            "category": "salary",
            "owner": "C01",
        }
        for m in range(1, 10)
    ]
    tx += [
        {
            "date": f"2026-{m:02d}-10",
            "amount": 90 * TR,
            "direction": "out",
            "desc": "HOC PHI",
            "category": "school",
            "owner": "C01",
        }
        for m in (1, 4, 8)
    ]
    tx += [
        {
            "date": "2026-03-01",
            "amount": 5 * TR,
            "direction": "out",
            "desc": "ONE OFF",
            "category": "other",
            "owner": "C01",
        }
    ]
    found = {(r["label"], r["cadence"]) for r in _calendar.recurring(tx)}
    assert found == {("Lương", "monthly"), ("Học phí", "quarterly")}


def test_the_calendar_places_maturities_coupons_instalments_and_flags_a_large_payment():
    mk = fixtures.market()
    rows = [
        h("deposit", 1 * TY, rate=0.05, opened="2025-12-01", maturity="2026-12-01"),
        h("loan", 2 * TY, kind="liability", monthly_payment=30 * TR, end="2027-12-01"),
    ]
    events = [{"date": "2027-03-15", "direction": "out", "amount": 1_800 * TR, "label": "Du học"}]
    cal = _calendar.build(rows, [], events, "2026-10-09", 12, 500 * TR, mk)
    months = {m["month"]: m for m in cal["months"]}
    assert cal["start"] == "2026-11" and len(cal["months"]) == 12
    assert months["2026-12"]["in"] == round(1 * TY * (1 + 0.05 * 365 / 365))
    assert all(m["out"] >= 30 * TR for m in cal["months"])
    assert [(x["month"], x["label"]) for x in cal["large"]] == [("2027-03", "Du học")]


def test_every_client_s_dashboard_builds_in_both_views():
    for cid in fixtures.client_ids():
        for scope in ("personal", "family"):
            out = asyncio.run(ENGINE.run(inputs={"client_id": cid, "scope": scope, "months": 24}))
            assert "$errors" not in out, (cid, out.get("$errors"))
            d = out["dashboard"]
            assert d["net_worth"]["value"] > 0 and len(d["cashflow"]["months"]) == 24
            assert abs(sum(a["share"] for a in d["allocation"]) - 1) < 1e-9
            assert d["headline"]["net_worth"].endswith(("tỷ", "triệu"))


def test_the_family_view_is_the_household_sum():
    def run(scope):
        out = asyncio.run(ENGINE.run(inputs={"client_id": "C01", "scope": scope, "months": 12}))
        return out["dashboard"]

    me, family = run("personal"), run("family")
    assert family["net_worth"]["value"] > me["net_worth"]["value"]
    assert family["profile"]["income_monthly"] == 120 * TR + 77 * TR


def test_the_services_answer_over_http():
    app = Application.find(".")
    with TestClient(app.asgi()) as client:
        listed = client.get("/api/clients").json()
        assert [c["id"] for c in listed["clients"]] == ["C01", "C02", "C03", "C04", "C05"]
        board = client.post("/api/dashboard", json={"client_id": "C04", "scope": "personal"})
        assert board.status_code == 200, board.text
        assert board.json()["dashboard"]["client_id"] == "C04"
        assert client.post("/api/dashboard", json={"client": "C04"}).json()["field"] == "client"  # not a parameter: 400
        bad = client.post("/api/dashboard", json={"client_id": "nobody"})
        assert bad.status_code == 500
        assert client.get("/").status_code == 200


def test_the_calendar_keeps_the_past_year_as_it_happened_and_this_month_apart():
    mk = fixtures.market()
    tx = [
        {"date": "2026-09-05", "amount": 120 * TR, "direction": "in", "desc": "LUONG T9", "category": "salary", "owner": "C01"},
        {"date": "2026-09-12", "amount": 3 * TR, "direction": "out", "desc": "THE GRAB", "category": "living", "owner": "C01"},
        {"date": "2024-01-05", "amount": 9 * TR, "direction": "in", "desc": "TOO OLD", "category": "salary", "owner": "C01"},
    ]
    cal = _calendar.build([], tx, [], "2026-10-09", 12, 500 * TR, mk)
    past = {m["month"]: m for m in cal["history"]}
    assert list(past) == [_calendar.month_add("2025-10", i) for i in range(12)]
    assert (past["2026-09"]["in"], past["2026-09"]["out"]) == (120 * TR, 3 * TR)
    assert {i["label"] for i in past["2026-09"]["items"]} == {"Lương", "Chi tiêu sinh hoạt"}
    assert sum(m["in"] for m in cal["history"]) == 120 * TR
    assert cal["current"]["month"] == "2026-10" and cal["months"][0]["month"] == "2026-11"


def test_a_holding_carries_when_and_at_what_it_was_bought():
    out = asyncio.run(ENGINE.run(inputs={"client_id": "C01", "scope": "personal", "months": 12}))
    by = {h["name"]: h for h in out["dashboard"]["holdings"]}
    fpt = by["Cổ phiếu FPT"]
    assert fpt["detail"]["bought"] and fpt["detail"]["avg_price"] and fpt["cost"] == fpt["detail"]["qty"] * fpt["detail"]["avg_price"]
    assert all(h["detail"].get("bought") for h in by.values() if h["class"] in ("stock", "bond", "fund"))


def test_a_card_balance_is_paid_once_not_every_month():
    mk = fixtures.market()
    tx = [
        {"date": f"2026-{m:02d}-25", "amount": 33 * TR, "direction": "out", "desc": "THANH TOAN DU NO THE TIN DUNG", "category": "card", "owner": "C01"}
        for m in range(1, 10)
    ]
    cal = _calendar.build([h("card", 45 * TR, kind="liability")], tx, [], "2026-10-09", 12, 500 * TR, mk)
    paid = [(m["month"], i["amount"]) for m in cal["months"] for i in m["items"] if i["kind"] == "card"]
    assert paid == [("2026-11", 45 * TR)]
    assert not cal["recurring"]
