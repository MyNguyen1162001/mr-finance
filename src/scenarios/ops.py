"""The scenario's steps: the request, the client's picture, the simulation (life or stress)."""

from __future__ import annotations

from typing import Any, Dict

from operonx import op

from scenarios import _sim
from wealth import fixtures, profile

NOTE = "Nội dung là mô phỏng; khuyến nghị cụ thể phải qua chuyên gia duyệt."


@op
def check_request(client_id: str = None, scenario: str = None, params: dict = None, scope: str = None) -> dict:
    """What a caller sent, checked: a known client and scenario, ``params`` an object."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    scenario = str(scenario or "")
    if scenario not in _sim.SCENARIOS:
        raise ValueError(f"no scenario {scenario!r}; one of {sorted(_sim.SCENARIOS)}")
    params = params or {}
    if not isinstance(params, dict):
        raise ValueError("params is an object")
    return {"client_id": client_id, "scenario": scenario, "params": params, "scope": scope or "personal"}


@op
def profile_of(client_id: str, members: list) -> dict:
    return {"profile": profile.build(client_id, members)}


@op
def kind_of(scenario: str) -> dict:
    """A life event the client tries, or a stress test the system runs."""
    return {"stress": _sim.SCENARIOS[scenario]["kind"] == "stress"}


def _run(client_id: str, scenario: str, params: Dict[str, Any], holdings: list, profile: dict) -> Dict[str, Any]:
    meta = _sim.SCENARIOS[scenario]
    pic = _sim.Pic(holdings=holdings, profile=profile, market=fixtures.market())
    out = meta["run"](pic, params or {})
    if out.get("goal") and scenario != "business_cash":  # an emergency is not tracked month by month
        out["goal"]["tracking"] = _sim.track(meta["run"], pic, out["params"], scenario)
    return {
        "client_id": client_id,
        "scenario": scenario,
        "kind": meta["kind"],
        "title": meta["title"],
        "question": meta["question"],
        "as_of": pic.market["as_of"],
        "note": NOTE,
        **out,
    }


@op
def life(client_id: str, scenario: str, params: dict, holdings: list, profile: dict) -> dict:
    """A life event, with the client's parameters (defaults from their own data)."""
    return {"result": _run(client_id, scenario, params, holdings, profile)}


@op
def stress(client_id: str, scenario: str, params: dict, holdings: list, profile: dict) -> dict:
    """A market shock applied to every holding, measured against the client's drawdown limit."""
    return {"result": _run(client_id, scenario, params, holdings, profile)}


@op
def answer(life_result: dict = None, stress_result: dict = None) -> dict:
    return {"result": life_result or stress_result}


@op
def check_client(client_id: str = None, scope: str = None) -> dict:
    """What a caller sent, checked: a known client, a scope."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    return {"client_id": client_id, "scope": scope or "personal"}


@op
def goals(client_id: str, holdings: list, profile: dict) -> dict:
    """Every life event read as a goal, on the client's own data with its default assumptions:
    what it needs, what the client has for it, the gap, a status and up to three actions. The ones
    fitting the client's persona are the ones followed until the client sets others."""
    pic = _sim.Pic(holdings=holdings, profile=profile, market=fixtures.market())
    out = []
    for sid, meta in _sim.SCENARIOS.items():
        if meta["kind"] != "life" or not meta.get("stage"):
            continue
        res = meta["run"](pic, {})
        out.append(
            {
                "id": sid,
                "title": meta["title"],
                "stage": meta["stage"],
                "stage_label": _sim.STAGES[meta["stage"]],
                "followed": profile["persona_hint"] in meta["personas"],
                "params": res["params"],
                "goal": res["goal"],
            }
        )
    return {"goals": out, "stages": _sim.STAGES, "as_of": pic.market["as_of"]}
