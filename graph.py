"""LangGraph StateGraph wiring: nodes, conditional edges, and compilation."""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents import generate_outreach, handle_error, research_account, sync_crm
from state import AgentState


def _route_on_status(state: AgentState) -> str:
    return "error" if state["execution_metadata"].get("status") == "error" else "success"


def _route_after_error(state: AgentState) -> str:
    metadata = state["execution_metadata"]
    if metadata.get("status") != "retry":
        return "exit"
    return metadata.get("resume_node", "research_account")


def build_graph(checkpointer=None) -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("research_account", research_account)
    graph.add_node("generate_outreach", generate_outreach)
    graph.add_node("sync_crm", sync_crm)
    graph.add_node("handle_error", handle_error)

    graph.set_entry_point("research_account")

    graph.add_conditional_edges(
        "research_account",
        _route_on_status,
        {"success": "generate_outreach", "error": "handle_error"},
    )
    graph.add_conditional_edges(
        "generate_outreach",
        _route_on_status,
        {"success": "sync_crm", "error": "handle_error"},
    )
    graph.add_conditional_edges(
        "handle_error",
        _route_after_error,
        # Retry resumes at the node that failed when its inputs are intact
        # (an outreach failure doesn't redo research); otherwise it restarts
        # from research_account, which every downstream step depends on.
        {"research_account": "research_account", "generate_outreach": "generate_outreach", "exit": END},
    )
    graph.add_edge("sync_crm", END)

    return graph.compile(checkpointer=checkpointer)
