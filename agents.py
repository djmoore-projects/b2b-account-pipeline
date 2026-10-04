"""Node implementations: research, outreach generation, and CRM sync.

Each node is wrapped with @timed_node, which records per-node latency into
state["execution_metadata"] and converts exceptions into a routable error
status instead of raising through the graph.
"""

from __future__ import annotations

import functools
import json
import logging
import os
import re
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from tavily import TavilyClient

from state import AgentState

logger = logging.getLogger("pipeline")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Claude Opus 4.8 by default. For latency-sensitive deployments (this demo's
# whole premise is speed), claude-sonnet-5 is a strong drop-in swap via
# ANTHROPIC_MODEL — near-Opus quality on agentic/tool-calling work at lower
# per-token cost and latency.
DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
MAX_TOOL_ITERATIONS = 3
MAX_SEARCHES = 3  # total web_search calls per research run, including parallel calls
MAX_RETRIES = 2


def get_llm(max_tokens: int = 4096) -> ChatAnthropic:
    return ChatAnthropic(model=DEFAULT_MODEL, max_tokens=max_tokens, timeout=60)


# ---------------------------------------------------------------------------
# Timing / error-handling decorator
# ---------------------------------------------------------------------------


def timed_node(name: str) -> Callable:
    """Wrap a node so it records duration + converts exceptions to a routable error."""

    def decorator(fn: Callable[[AgentState], dict]) -> Callable[[AgentState], dict]:
        @functools.wraps(fn)
        def wrapper(state: AgentState) -> dict:
            metadata = dict(state.get("execution_metadata") or {})
            durations = dict(metadata.get("node_durations", {}))
            errors = list(metadata.get("errors", []))

            start = time.perf_counter()
            try:
                update = fn(state)
            except Exception as exc:
                durations[name] = time.perf_counter() - start
                errors.append(f"{name}: {exc}")
                logger.exception("Node '%s' failed", name)
                metadata.update(
                    node_durations=durations,
                    errors=errors,
                    status="error",
                    last_error_node=name,
                )
                return {"execution_metadata": metadata}

            durations[name] = time.perf_counter() - start
            metadata.update(node_durations=durations, errors=errors, status="ok")
            update["execution_metadata"] = metadata
            return update

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Tavily search tool
# ---------------------------------------------------------------------------

_tavily_client: TavilyClient | None = None


def _get_tavily_client() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY environment variable is not set")
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


@tool
def web_search(query: str) -> str:
    """Search the web for recent company news, funding rounds, product launches,
    and leadership. Use specific, targeted queries (e.g. "Acme Corp Series B funding
    2026" rather than just "Acme Corp")."""
    client = _get_tavily_client()
    response = client.search(query=query, search_depth="basic", max_results=5)
    results = response.get("results", [])
    if not results:
        return f"No results found for query: {query}"
    formatted = [
        f"- {r['title']}: {r['content'][:300]} (source: {r['url']})" for r in results
    ]
    return "\n".join(formatted)


# ---------------------------------------------------------------------------
# Structured output schemas
# ---------------------------------------------------------------------------


class Persona(BaseModel):
    name: str = Field(description='Full name as it appears in the search results, or "Unknown" if not found')
    title: str = Field(description="Job title / role")
    relevance: str = Field(description="Why this person matters for outreach, e.g. economic buyer, champion")


class ResearchData(BaseModel):
    company_name: str
    industry: str = Field(description="Best-guess industry / vertical")
    recent_funding: str | None = Field(default=None, description="Most recent funding round and amount, if found")
    recent_news: list[str] = Field(default_factory=list, description="2-5 recent, notable news bullet points")
    key_personas: list[Persona] = Field(default_factory=list, description="1-3 likely buying-committee contacts")
    summary: str = Field(description="2-3 sentence synthesis an SDR could read in 10 seconds")


class OutreachStep(BaseModel):
    step_number: int
    channel: Literal["email", "linkedin"]
    subject: str | None = Field(default=None, description="Email subject line; null for LinkedIn steps")
    body: str = Field(description="Message body, personalized using the research data")


class OutreachSequence(BaseModel):
    steps: list[OutreachStep] = Field(
        description="Exactly 3 steps in order: email, linkedin connection request, follow-up email"
    )


# ---------------------------------------------------------------------------
# Node: research_account
# ---------------------------------------------------------------------------

RESEARCH_SYSTEM_PROMPT = """You are a B2B account research analyst. Use the \
web_search tool to gather recent, specific information about the target company: \
funding history, recent news/product launches, and likely buying-committee personas \
(titles, not necessarily named individuals if names aren't findable). You have a budget \
of at most 3 searches in total, so make each query count. Once you have enough to write a \
useful briefing, stop searching and summarize.

Only report facts that the search results attribute to this exact company. Results about \
similarly named companies are not evidence; don't borrow their people, funding, or news. If \
you can't find reliable information about the target, say so plainly in the summary, leave \
funding and news empty, and list personas by likely title with the name "Unknown"."""


@timed_node("research_account")
def research_account(state: AgentState) -> dict:
    company = state["company_name"]
    llm = get_llm()
    llm_with_tools = llm.bind_tools([web_search])

    messages = [
        SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
        HumanMessage(content=f"Research the company: {company}"),
    ]

    searches = 0
    for _ in range(MAX_TOOL_ITERATIONS):
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        if not response.tool_calls:
            break
        # Claude can request several searches in one turn, so the iteration cap alone
        # doesn't bound search count. Every tool_call still needs a ToolMessage reply.
        for tool_call in response.tool_calls:
            if searches >= MAX_SEARCHES:
                result = "Search budget exhausted. Summarize using the results you already have."
            else:
                result = web_search.invoke(tool_call["args"])
                searches += 1
            messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
        if searches >= MAX_SEARCHES:
            break

    structured_llm = get_llm().with_structured_output(ResearchData)
    research: ResearchData = structured_llm.invoke(
        messages + [HumanMessage(content="Summarize your findings into the required structured format.")]
    )

    logger.info("Research complete for %s: %d personas found", company, len(research.key_personas))
    return {"research_data": research.model_dump()}


# ---------------------------------------------------------------------------
# Node: generate_outreach
# ---------------------------------------------------------------------------

OUTREACH_SYSTEM_PROMPT = """You are an SDR writing a highly personalized, 3-step \
outreach sequence: (1) an initial email, (2) a LinkedIn connection request note, \
(3) a brief follow-up email. Reference specific details from the research data \
(funding, news, persona context) — avoid generic templates. Keep emails under 120 \
words and the LinkedIn note under 300 characters.

Every factual statement about the company must come from the research data; do not \
add numbers, launches, or claims that aren't in it. Address each message to a persona \
from the research data. These messages are sent as-is: never use placeholders like \
[Name] or [Your Name], and sign emails off with just "Best,"."""

EXPECTED_CHANNELS = ["email", "linkedin", "email"]
MAX_EMAIL_WORDS = 120
MAX_LINKEDIN_CHARS = 300
_PLACEHOLDER = re.compile(r"\[[^\]]{1,40}\]|\{\{.*?\}\}")


def outreach_violations(steps: list[OutreachStep]) -> list[str]:
    """Check the sequence against the outreach contract. Prompted limits drift; this doesn't."""
    problems = []
    channels = [s.channel for s in steps]
    if channels != EXPECTED_CHANNELS:
        problems.append(f"channels must be {EXPECTED_CHANNELS}, got {channels}")
    for i, step in enumerate(steps, start=1):
        if step.channel == "email":
            words = len(step.body.split())
            if words > MAX_EMAIL_WORDS:
                problems.append(f"step {i} email is {words} words; max is {MAX_EMAIL_WORDS}")
            if not step.subject:
                problems.append(f"step {i} email needs a subject line")
        elif len(step.body) > MAX_LINKEDIN_CHARS:
            problems.append(f"step {i} LinkedIn note is {len(step.body)} chars; max is {MAX_LINKEDIN_CHARS}")
        if placeholders := _PLACEHOLDER.findall(step.body + " " + (step.subject or "")):
            problems.append(f"step {i} contains unfilled placeholders {placeholders}")
    return problems


@timed_node("generate_outreach")
def generate_outreach(state: AgentState) -> dict:
    research_data = state["research_data"]
    llm = get_llm().with_structured_output(OutreachSequence)

    prompt = (
        f"Company: {state['company_name']}\n"
        f"Research data:\n{json.dumps(research_data, indent=2)}\n\n"
        "Write the 3-step outreach sequence."
    )
    messages = [SystemMessage(content=OUTREACH_SYSTEM_PROMPT), HumanMessage(content=prompt)]
    sequence: OutreachSequence = llm.invoke(messages)

    # One targeted repair pass if the draft breaks the contract.
    problems = outreach_violations(sequence.steps)
    if problems:
        logger.warning("Outreach draft violated contract, repairing: %s", problems)
        draft = json.dumps([step.model_dump() for step in sequence.steps], indent=2)
        sequence = llm.invoke(messages + [HumanMessage(content=(
            f"Your draft:\n{draft}\n\nFix these problems and return the full corrected sequence:\n- "
            + "\n- ".join(problems)
        ))])
        if remaining := outreach_violations(sequence.steps):
            logger.warning("Outreach still violates contract after repair: %s", remaining)

    logger.info("Generated %d-step outreach sequence", len(sequence.steps))
    return {"outreach_sequence": [step.model_dump() for step in sequence.steps]}


# ---------------------------------------------------------------------------
# Node: sync_crm (mock HubSpot-style client)
# ---------------------------------------------------------------------------


class MockCRMClient:
    """Simulates a HubSpot-like contact/deal upsert API for demo purposes."""

    def __init__(self, latency_seconds: float = 0.3, store_path: Path | None = None):
        self._latency_seconds = latency_seconds
        self._store_path = store_path or Path(__file__).parent / "crm_mock_store.json"

    def upsert_contact_and_deal(self, payload: dict) -> dict:
        time.sleep(self._latency_seconds)  # simulate network round-trip

        record = dict(payload)
        record["id"] = f"crm_{uuid.uuid4().hex[:10]}"
        record["synced_at"] = datetime.now(timezone.utc).isoformat()

        records = self._load()
        records.append(record)
        self._save(records)

        return {"status": "synced", "record_id": record["id"]}

    def _load(self) -> list:
        if self._store_path.exists():
            return json.loads(self._store_path.read_text())
        return []

    def _save(self, records: list) -> None:
        self._store_path.write_text(json.dumps(records, indent=2))


@timed_node("sync_crm")
def sync_crm(state: AgentState) -> dict:
    payload = {
        "company_name": state["company_name"],
        "industry": state["research_data"].get("industry"),
        "summary": state["research_data"].get("summary"),
        "key_personas": state["research_data"].get("key_personas", []),
        "outreach_sequence": state["outreach_sequence"],
    }
    crm = MockCRMClient()
    result = crm.upsert_contact_and_deal(payload)

    logger.info("CRM sync complete: %s", result["record_id"])
    return {"crm_status": result["status"]}


# ---------------------------------------------------------------------------
# Node: handle_error
# ---------------------------------------------------------------------------


def handle_error(state: AgentState) -> dict:
    """Not @timed_node: this node manages the retry/exit decision itself."""
    metadata = dict(state.get("execution_metadata") or {})
    retry_count = metadata.get("retry_count", 0) + 1
    metadata["retry_count"] = retry_count

    if retry_count <= MAX_RETRIES:
        metadata["status"] = "retry"
        # Resume where it failed if that node's inputs are already in state; only
        # fall back to re-running research when research itself didn't complete.
        failed_node = metadata.get("last_error_node")
        research_done = bool(state.get("research_data"))
        metadata["resume_node"] = (
            failed_node if failed_node == "generate_outreach" and research_done else "research_account"
        )
        logger.warning(
            "Error in '%s' — retrying pipeline (attempt %d/%d)",
            metadata.get("last_error_node", "unknown"),
            retry_count,
            MAX_RETRIES,
        )
        return {"execution_metadata": metadata}

    metadata["status"] = "failed"
    logger.error("Max retries (%d) exceeded — exiting pipeline", MAX_RETRIES)
    return {"execution_metadata": metadata, "crm_status": "failed"}
