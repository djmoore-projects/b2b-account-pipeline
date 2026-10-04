"""Shared state definition for the account research & outreach graph."""

from __future__ import annotations

from typing import Any, TypedDict


class ExecutionMetadata(TypedDict, total=False):
    """Bookkeeping carried alongside the business state.

    Not part of the LangGraph business schema per se, but threaded through
    the state so every node can read/append to it without a side-channel.
    """

    node_durations: dict[str, float]
    errors: list[str]
    retry_count: int
    status: str  # "ok" | "error" | "retry" | "failed"
    last_error_node: str
    resume_node: str  # where handle_error routes a retry


class AgentState(TypedDict):
    """State passed between every node in the pipeline."""

    company_name: str
    research_data: dict[str, Any]
    outreach_sequence: list[dict[str, Any]]
    crm_status: str
    execution_metadata: ExecutionMetadata
