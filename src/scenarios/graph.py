"""scenario_flow: the client's picture → a life event or a stress test → numbers and two options."""

from operonx import END, START, graph
from operonx.core.ops import if_

from consolidate.graph import consolidate_flow
from scenarios.ops import answer, check_client, check_request, goals, kind_of, life, profile_of, stress


@graph
def scenario_flow(client_id, scenario, params=None, scope="personal"):
    """One simulation, on this client's own holdings (POST /api/scenario)."""
    ask = check_request(client_id=client_id, scenario=scenario, params=params, scope=scope)
    client_id, scenario, params, scope = ask["client_id"], ask["scenario"], ask["params"], ask["scope"]
    held = consolidate_flow(client_id=client_id, scope=scope)
    who = profile_of(client_id=client_id, members=held["members"])
    kind = kind_of(scenario=scenario)
    tried = life(
        client_id=client_id, scenario=scenario, params=params, holdings=held["holdings"], profile=who["profile"]
    )
    shocked = stress(
        client_id=client_id, scenario=scenario, params=params, holdings=held["holdings"], profile=who["profile"]
    )
    out = answer(life_result=tried["result"], stress_result=shocked["result"])
    START >> ask >> held >> who >> kind >> if_(kind["stress"] == True, shocked).else_(tried)  # noqa: E712
    tried >> out
    shocked >> out
    out >> END


@graph
def goals_flow(client_id, scope="personal"):
    """Every life goal of a client, with its gap and status (POST /api/goals)."""
    ask = check_client(client_id=client_id, scope=scope)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    who = profile_of(client_id=ask["client_id"], members=held["members"])
    out = goals(client_id=ask["client_id"], holdings=held["holdings"], profile=who["profile"])
    START >> ask >> held >> who >> out >> END
