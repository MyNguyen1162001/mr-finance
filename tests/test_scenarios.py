import asyncio

from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient

from review.graph import review_flow
from scenarios import _sim
from scenarios.graph import scenario_flow
from wealth import fixtures, store
from wealth.money import TR, TY

ENGINE = Operon(scenario_flow, params={"client_id": None, "scenario": None, "params": None, "scope": None})


def sim(client_id, scenario, params=None, scope="personal"):
    out = asyncio.run(
        ENGINE.run(inputs={"client_id": client_id, "scenario": scenario, "params": params or {}, "scope": scope})
    )
    assert "$errors" not in out, (client_id, scenario, out.get("$errors"))
    return out["result"]


def test_the_money_maths():
    assert round(_sim.pmt(1 * TY, 0.12, 1)) == round(1 * TY * 0.01 / (1 - 1.01**-12))
    assert _sim.pmt(1_200, 0, 1) == 100
    monthly = _sim.saving_for(120 * TR, 12, 0)
    assert monthly == 10 * TR


def test_every_scenario_runs_for_every_client_in_both_views():
    for cid in fixtures.client_ids():
        for scope in ("personal", "family"):
            for sid, meta in _sim.SCENARIOS.items():
                r = sim(cid, sid, scope=scope)
                assert r["kind"] == meta["kind"] and r["summary"], (cid, sid)
                assert {"net_worth", "liquid", "liquid_months"} <= set(r["before"])
                if r["options"]:
                    assert [o["id"] for o in r["options"]] == ["light", "heavy"]
                    assert all(o["actions"] and o["effect"] for o in r["options"])


def test_a_stress_test_measures_against_the_drawdown_limit():
    r = sim("C03", "vni_30")
    assert r["loss_share"] > 0.15 and any("vượt ngưỡng" in line["value"] for line in r["summary"])
    calm = sim("C04", "vni_30")
    assert calm["loss_share"] < 0.02, "a retiree with no stocks barely moves"


def test_parameters_change_the_answer():
    cheap = sim("C05", "leverage_buy", {"price": 3 * TY})
    dear = sim("C05", "leverage_buy", {"price": 6 * TY})
    assert cheap["params"]["price"] == 3 * TY
    value = lambda r, label: next(line["value"] for line in r["summary"] if line["label"] == label)  # noqa: E731
    assert value(cheap, "Trả góp mỗi tháng") != value(dear, "Trả góp mỗi tháng")


def test_selling_a_second_home_needs_one():
    assert sim("C01", "sell_home")["options"] == []
    family = sim("C01", "sell_home", scope="family")
    assert family["params"]["name"].startswith("Căn hộ Phú Mỹ Hưng") and family["options"]


def test_an_option_waits_for_the_rm_and_is_decided_once():
    app = Application.find(".")
    with TestClient(app.asgi()) as client:
        r = client.post("/api/scenario", json={"client_id": "C02", "scenario": "business_cash"}).json()["result"]
        item = client.post(
            "/api/review/propose",
            json={
                "client_id": "C02",
                "scenario": "business_cash",
                "title": r["title"],
                "option": r["options"][0],
                "summary": r["summary"],
            },
        ).json()["item"]
        assert item["status"] == "pending" and item["title"].startswith("Doanh nghiệp cần vốn gấp")
        queue = client.get("/api/review", params={"status": "pending"}).json()["items"]
        assert [q["id"] for q in queue] == [item["id"]] and queue[0]["client_name"] == "Lê Văn Phát"
        done = client.post(
            "/api/review/decide", json={"item_id": item["id"], "decision": "approved", "note": "OK"}
        ).json()["item"]
        assert (done["status"], done["note"]) == ("approved", "OK")
        again = client.post("/api/review/decide", json={"item_id": item["id"], "decision": "rejected"})
        assert again.status_code == 500, "a decided item is not decided again"
        assert client.get("/api/scenarios").json()["scenarios"][0]["id"] == "tuition"


def test_review_flow_refuses_an_unknown_item():
    out = asyncio.run(
        Operon(review_flow, params={"item_id": None, "decision": None, "note": None}).run(
            inputs={"item_id": "R-nope", "decision": "approved", "note": ""}
        )
    )
    assert "item" not in out and any(e["type"] == "ValueError" for e in out["$errors"].values())
    assert store.reviews() == []


def test_every_client_has_goals_with_a_gap_a_status_and_ranked_actions():
    from scenarios.graph import goals_flow

    engine = Operon(goals_flow, params={"client_id": None, "scope": None})
    for cid in fixtures.client_ids():
        out = asyncio.run(engine.run(inputs={"client_id": cid, "scope": "family"}))
        assert "$errors" not in out, out.get("$errors")
        assert out["goals"] and any(g["followed"] for g in out["goals"]), cid
        for g in out["goals"]:
            x = g["goal"]
            assert x["status"] in ("on_track", "at_risk", "off_track")
            assert x["gap"] == x["need"] - x["have"] or x["have"] == 0
            assert len(x["actions"]) <= 3
            cuts = [a["cut"] for a in x["actions"]]
            assert cuts == sorted(cuts, reverse=True)


def test_a_tried_assumption_moves_the_goal():
    base = sim("C01", "tuition")["goal"]
    dearer = sim("C01", "tuition", {"per_year": 3 * TY})["goal"]
    assert dearer["need"] > base["need"] and dearer["gap"] > base["gap"]
