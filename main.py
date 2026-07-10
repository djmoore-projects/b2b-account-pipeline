"""Entry point: runs the pipeline for a company and prints a benchmark report.

Usage:
    python main.py "Acme Corp"
"""

from __future__ import annotations

import logging
import sys
import time
import uuid

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

from graph import build_graph
from state import AgentState

BASELINE_SECONDS = 45 * 60  # manual account research, per the project's target metric

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")


def _initial_state(company_name: str) -> AgentState:
    return {
        "company_name": company_name,
        "research_data": {},
        "outreach_sequence": [],
        "crm_status": "pending",
        "execution_metadata": {
            "node_durations": {},
            "errors": [],
            "retry_count": 0,
            "status": "ok",
        },
    }


def _print_report(company_name: str, final_state: AgentState, elapsed_seconds: float) -> None:
    metadata = final_state.get("execution_metadata", {})
    durations = metadata.get("node_durations", {})

    print("=" * 64)
    print(f"ACCOUNT RESEARCH & OUTREACH PIPELINE — {company_name}")
    print("=" * 64)
    print("Node timing breakdown:")
    for node_name, duration in durations.items():
        print(f"  {node_name:<20} {duration:6.2f}s")
    print("-" * 64)

    failed = metadata.get("status") == "failed" or final_state.get("crm_status") == "failed"
    if failed:
        print(f"FAILED: pipeline did not complete after {elapsed_seconds:.2f}s")
        for error in metadata.get("errors", []):
            print(f"  - {error}")
    else:
        speedup = BASELINE_SECONDS / elapsed_seconds if elapsed_seconds > 0 else float("inf")
        print(
            f"SUCCESS: Account processed in {elapsed_seconds:.2f} seconds "
            f"(Optimized from 45 minutes, ~{speedup:,.0f}x faster)"
        )
        print(f"CRM status: {final_state.get('crm_status')}")
    print("=" * 64)


def run_pipeline(company_name: str) -> AgentState:
    with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        app = build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        logger.info("Starting pipeline for '%s'", company_name)
        start = time.perf_counter()
        final_state: AgentState = app.invoke(_initial_state(company_name), config=config)
        elapsed = time.perf_counter() - start

    _print_report(company_name, final_state, elapsed)
    return final_state


if __name__ == "__main__":
    load_dotenv()
    target_company = sys.argv[1] if len(sys.argv) > 1 else "Anthropic"
    run_pipeline(target_company)
