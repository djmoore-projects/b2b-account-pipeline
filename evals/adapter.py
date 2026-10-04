"""agent-reliability-harness adapter for the account research pipeline.

Runs the real compiled graph (live Claude + Tavily) with the harness tracer
attached through LangChain callbacks. Nothing in the pipeline is mocked except
where the pipeline mocks it itself (the CRM). Each task gets its own CRM store
so the harness can grade what was actually written, not just what the state
claims was written.
"""

from __future__ import annotations

import contextvars
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import agents  # noqa: E402
from graph import build_graph  # noqa: E402
from main import _initial_state  # noqa: E402

_CRM_STORE: contextvars.ContextVar[Path] = contextvars.ContextVar("crm_store")
_OriginalCRM = agents.MockCRMClient


class _IsolatedCRMClient(_OriginalCRM):
    """Same client, but writes to this task's store so parallel tasks can't collide."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("store_path", _CRM_STORE.get(None))
        super().__init__(*args, **kwargs)


agents.MockCRMClient = _IsolatedCRMClient


def run(task_input: dict, tracer) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "crm.json"
        token = _CRM_STORE.set(store)
        try:
            app = build_graph()
            final = app.invoke(
                _initial_state(task_input["company_name"]),
                config={"callbacks": tracer.callbacks, "recursion_limit": 25},
            )
        finally:
            _CRM_STORE.reset(token)
        records = json.loads(store.read_text()) if store.exists() else []
    return {"state": final, "env": {"crm_records": records}}
