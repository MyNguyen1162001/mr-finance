"""The web app beside the graphs: the UI (web/) and the plain reads it needs.

Listing the sample clients or resetting the demo is not a computation, so it is not a graph:
it is served here, by the asgi service app/main.py mounts last.
"""

from __future__ import annotations

import json
from functools import lru_cache

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from scenarios._sim import SCENARIOS
from wealth import fixtures, store
from wealth.paths import DATA, ROOT


async def clients(request: Request) -> JSONResponse:
    out = []
    for cid in fixtures.client_ids():
        c = fixtures.client(cid)
        out.append(
            {
                **fixtures.summary(cid),
                "household": [{**m, "name": fixtures.client(m["id"])["name"]} for m in c.get("household", [])],
                "samples": c.get("samples", []),
            }
        )
    return JSONResponse({"clients": out, "as_of": fixtures.market()["as_of"]})


async def healthz(request: Request) -> JSONResponse:
    # operonx leaves /healthz to the asgi app when one is mounted at "/"
    return JSONResponse({"ok": True})


async def scenarios(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "scenarios": [
                {"id": k, "kind": v["kind"], "title": v["title"], "question": v["question"], "personas": v["personas"]}
                for k, v in SCENARIOS.items()
            ]
        }
    )


async def reviews(request: Request) -> JSONResponse:
    """The RM queue (newest first), for one client or all, by status."""
    q = request.query_params
    rows = store.reviews(client_id=q.get("client_id") or None, status=q.get("status") or None)
    names = {cid: fixtures.client(cid)["name"] for cid in fixtures.client_ids(members=True)}
    return JSONResponse({"items": [{**r, "client_name": names.get(r["client_id"], r["client_id"])} for r in rows]})


@lru_cache(maxsize=1)
def _advisory() -> dict:
    return json.loads((DATA / "advisory.json").read_text(encoding="utf-8"))


async def advisory(request: Request) -> JSONResponse:
    """A client's specialist team and advisory track record (data/advisory.json, mock), with the
    risk test they took in the demo, if any, as the last point of their risk-appetite history."""
    cid = request.query_params.get("client_id") or ""
    data = _advisory()
    if cid not in data["team"]:
        return JSONResponse({"error": f"no client {cid!r}"}, status_code=404)
    track = json.loads(json.dumps(data["tracking"][cid]))
    test = store.result(cid, "risk")
    if test:
        track["risk_tests"].append(
            {
                "date": test.get("taken"),
                "tolerance": round(test["tolerance"]),
                "capacity": round(test["capacity"]),
                "profile": (test.get("profile") or {}).get("name"),
                "live": True,
            }
        )
    return JSONResponse({"team": data["team"][cid], "tracking": track, "as_of": data["as_of"], "note": data["note"]})


async def advisory_all(request: Request) -> JSONResponse:
    """The advisory track record over every client (data/advisory.json, mock): the totals, each AI's
    average score and trend, one row per client, the latest advice and the news missed for anyone."""
    data = _advisory()
    tracks = data["tracking"]
    names = {cid: fixtures.client(cid)["name"] for cid in tracks}
    keys = next(iter(tracks.values()))["summary"].keys()
    summary = {k: sum(t["summary"][k] for t in tracks.values()) for k in keys}
    agents = []
    for i, a in enumerate(next(iter(tracks.values()))["agents"]):
        mine = [t["agents"][i] for t in tracks.values()]
        n = len(mine)
        agents.append(
            {
                "id": a["id"],
                "name": a["name"],
                "name_vi": a["name_vi"],
                "score": round(sum(x["score"] for x in mine) / n),
                "trend": [round(sum(x["trend"][j] for x in mine) / n, 3) for j in range(len(a["trend"]))],
                "by_client": [{"client": names[c], "score": t["agents"][i]["score"]} for c, t in tracks.items()],
            }
        )
    clients = [
        {
            "id": cid,
            "name": names[cid],
            **t["summary"],
            "scores": {a["id"]: a["score"] for a in t["agents"]},
            "alerts_opened": t["engagement"]["alerts_opened"],
        }
        for cid, t in tracks.items()
    ]
    advice = sorted(
        ({**x, "client": names[cid]} for cid, t in tracks.items() for x in t["advice"]),
        key=lambda x: x["date"],
        reverse=True,
    )
    missed: dict = {}
    for cid, t in tracks.items():
        for n in t["missed_news"]:
            m = missed.setdefault(n["title"], {**n, "impact": 0.0, "clients": []})
            m["impact"] += n["impact"]
            m["clients"].append(names[cid])
    months = next(iter(tracks.values()))["engagement"]["months"]
    engagement = {
        "months": months,
        **{
            k: [round(sum(t["engagement"][k][j] for t in tracks.values()) / len(tracks)) for j in range(len(months))]
            for k in ("minutes", "days")
        },
    }
    return JSONResponse(
        {
            "summary": summary,
            "agents": agents,
            "clients": clients,
            "advice": advice,
            "missed_news": sorted(missed.values(), key=lambda m: m["impact"]),
            "engagement": engagement,
            "as_of": data["as_of"],
            "note": data["note"],
        }
    )


@lru_cache(maxsize=1)
def _views() -> dict:
    return json.loads((DATA / "views.json").read_text(encoding="utf-8"))


async def views(request: Request) -> JSONResponse:
    """House views beside the headlines (data/views.json, mock): what research houses expect, and
    which holdings each is about — the page matches them to the client's own."""
    return JSONResponse(_views())


async def reset(request: Request) -> JSONResponse:
    store.reset()
    return JSONResponse({"reset": True})


app = Starlette(
    routes=[
        Route("/healthz", healthz),
        Route("/api/clients", clients),
        Route("/api/scenarios", scenarios),
        Route("/api/review", reviews),
        Route("/api/advisory", advisory),
        Route("/api/advisory/all", advisory_all),
        Route("/api/views", views),
        Route("/api/reset", reset, methods=["POST"]),
        # the sample statements a demo uploads
        Mount("/samples", app=StaticFiles(directory=DATA / "samples"), name="samples"),
        Mount("/", app=StaticFiles(directory=ROOT / "web", html=True), name="web"),
    ]
)
