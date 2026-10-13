"""Mr. Finance: the whole picture of a client's wealth, and what is moving it.

POST /api/dashboard {client_id, scope?, months?} ──► dashboard_flow ──► the dashboard
POST /api/statement {client_id, filename, content} ──► statement_flow ──► holdings read (AI or rules)
POST /api/declare   {client_id, message, session_id} ──► declare_flow ──► the chat's reply, what it recorded
POST /api/risk      {client_id, answers} ──► risk_flow ──► the next question, or the profile
POST /api/alerts    {client_id, scope?} ──► alerts_flow ──► policies, macro, infrastructure, in VND
POST /api/scenario  {client_id, scenario, params?} ──► scenario_flow ──► numbers, a light and a heavy option
POST /api/goals     {client_id, scope?} ──► goals_flow ──► every life goal: need, have, gap, status, actions
POST /api/review/propose ──► propose_flow (the RM queue) · POST /api/review/decide ──► review_flow
07:00 daily, and `operonx run policy_sweep` ──► the policy_sweep job: alerts_flow for every client
GET  /api/clients, /api/advisory[/all], /api/views, POST /api/reset, GET / ──► app/web.py (the sample
     clients, the specialist team, the advisory track record, the house views, the UI)

Each service runs its graph as is: the JSON body fills the graph's parameters, and the reply is
its outputs (`{"dashboard": ...}`, `{"read": ...}`, ...). Every service and job of the product is
declared here; operonx.toml only points at `APP`.
"""

from operonx.app import Application, Eval, Service, asgi, env, http, schedule
from operonx.app.evals import Gate
from operonx.app.jobs import Job

from app import web
from dashboard.graph import dashboard_flow
from declare.graph import declare_flow
from impact.graph import alerts_flow
from impact.ops import every_client
from review.graph import propose_flow, review_flow
from risk.graph import risk_flow
from scenarios.graph import goals_flow, scenario_flow
from statements.checks import items_match
from statements.graph import sample_flow, statement_flow

PORT = env("PORT", 8030)

APP = Application(
    "mr-finance",
    description="Consolidate every asset a client holds, anywhere, into one picture — and say what is moving it.",
    services=[
        Service(
            "dashboard",
            http("POST", "/api/dashboard", port=PORT),
            graph=dashboard_flow,
            description="POST {client_id, scope: personal|family, months}: the dashboard.",
        ),
        Service(
            "statement",
            http("POST", "/api/statement", port=PORT),
            graph=statement_flow,
            description="POST {client_id, filename, content: base64}: a statement, read and kept.",
        ),
        Service(
            "declare",
            http("POST", "/api/declare", port=PORT),
            graph=declare_flow,
            description="POST {client_id, message, session_id}: one chat turn of declarations.",
        ),
        Service(
            "risk",
            http("POST", "/api/risk", port=PORT),
            graph=risk_flow,
            description="POST {client_id, answers}: the next question of the risk test, or its result.",
        ),
        Service(
            "alerts",
            http("POST", "/api/alerts", port=PORT),
            graph=alerts_flow,
            description="POST {client_id, scope?}: what is moving the client's wealth, in VND, with sources.",
        ),
        Service(
            "scenario",
            http("POST", "/api/scenario", port=PORT),
            graph=scenario_flow,
            description="POST {client_id, scenario, params?, scope?}: a life event or a stress test, with two options.",
        ),
        Service(
            "goals",
            http("POST", "/api/goals", port=PORT),
            graph=goals_flow,
            description="POST {client_id, scope?}: every life goal, with its gap, status and actions.",
        ),
        Service(
            "propose",
            http("POST", "/api/review/propose", port=PORT),
            graph=propose_flow,
            description="POST {client_id, scenario, title, option}: an option sent to the RM queue.",
        ),
        Service(
            "decide",
            http("POST", "/api/review/decide", port=PORT),
            graph=review_flow,
            description="POST {item_id, decision: approved|rejected, note?}: the RM's decision.",
        ),
        # last: it is mounted at "/", and would answer every path the services above own
        Service("web", asgi("/", port=PORT), app=web.app, description="The UI and the sample clients."),
    ],
    jobs=[
        # every client's alerts again: at 07:00 daily, before the RMs start (inside `operonx serve`),
        # and on demand with `operonx run policy_sweep`
        Job(
            "policy_sweep",
            graph=alerts_flow,
            items=every_client,
            key="client_id",
            schedule=schedule(at="07:00", port=PORT),
            description="07:00 daily: the policy sweep over every client.",
        ),
        # how well statements are read: `operonx run statement_reading` (exit code: the gate's).
        # The three demo samples must pass; the free-text note needs a model (MF_AI=on).
        Eval(
            "statement_reading",
            graph=sample_flow,
            input="filename",
            dataset="dataset:statements",
            evaluators=[items_match],
            gate=Gate(threshold=0.8),
        ),
    ],
)
