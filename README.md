# B2B Account Research & Outreach Pipeline

[![CI](https://github.com/djmoore-projects/b2b-account-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/djmoore-projects/b2b-account-pipeline/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Built with LangGraph](https://img.shields.io/badge/built%20with-LangGraph-1C3C3C)](https://github.com/langchain-ai/langgraph)

A multi-agent pipeline built on **LangGraph** that turns a company name into
a researched account brief, a personalized 3-step outreach sequence, and a
synced CRM record — end to end, in a single graph run.

**The metric this project proves:** manual B2B account research typically
takes an SDR **~45 minutes** (search company news, identify funding, find
buying-committee contacts, draft outreach, log it in the CRM). This pipeline
does the same job in **~60-90 seconds**, verified end-to-end against the
live Anthropic + Tavily APIs — see the real output below.

## Why this exists

Most "AI SDR" demos are a single prompt wrapped in a chat UI. This is the
opposite: a typed, stateful, checkpointed **graph** — real tool calling, real
structured-output contracts between steps, and a real error-handling edge
that retries and degrades gracefully instead of crashing on the first flaky
API call. It's meant to be a clear, readable reference for how to structure
a production multi-agent workflow with LangGraph, not just a proof of
concept.

## Architecture

```
                    ┌──────────────────────┐
        ┌──success──│  research_account     │◄────────┐
        │           └──────────┬────────────┘         │
        │                      │ error                 │ retry (≤2)
        │                      ▼                       │
        │           ┌──────────────────────┐           │
        │           │     handle_error      │───────────┘
        │           └──────────┬────────────┘
        │                      │ exit (retries exhausted)
        ▼                      ▼
┌──────────────────────┐     END (failed)
│   generate_outreach    │──error──► handle_error
└──────────┬─────────────┘
           │ success
           ▼
┌──────────────────────┐
│       sync_crm          │──► END (success)
└──────────────────────┘
```

- **`research_account`** — Claude, bound to a Tavily web-search tool, runs a
  bounded tool-calling loop (≤3 iterations) to gather recent funding, news,
  and likely buying-committee personas, then extracts the findings into a
  structured `ResearchData` object via `with_structured_output`.
- **`generate_outreach`** — Takes the structured research and synthesizes a
  3-step sequence (email → LinkedIn connection note → follow-up email),
  again via structured output so the shape is guaranteed, not just prompted.
- **`sync_crm`** — Formats the research + outreach into a CRM payload and
  upserts it through `MockCRMClient`, a local stand-in for a HubSpot-style
  contacts/deals API (simulated latency, JSON-file persistence).
- **`handle_error`** — Any node exception is caught by the `@timed_node`
  decorator, converted into `execution_metadata.status = "error"`, and
  routed here instead of crashing the run. `handle_error` retries from
  `research_account` up to `MAX_RETRIES` (default 2) times, then exits
  gracefully to `END` with `crm_status = "failed"` and every error message
  preserved in `execution_metadata.errors`.

### State

```python
class AgentState(TypedDict):
    company_name: str
    research_data: dict[str, Any]
    outreach_sequence: list[dict[str, Any]]
    crm_status: str
    execution_metadata: ExecutionMetadata  # node_durations, errors, retry_count, status
```

Nodes return **partial updates** — LangGraph merges them into state — keeping
each node function small and side-effect-free with respect to fields it
doesn't own.

### Persistence

The graph compiles with a `SqliteSaver` checkpointer, so every node
transition is durably persisted per `thread_id`. This is a real
`StateGraph.compile(checkpointer=...)` — nothing about the state machine is
mocked — so a run can be resumed, inspected, or replayed from any checkpoint
using LangGraph's standard checkpoint APIs.

## Quickstart

```bash
git clone https://github.com/djmoore-projects/b2b-account-pipeline.git
cd b2b-account-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY and TAVILY_API_KEY

python main.py "Acme Corp"
```

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API access |
| `TAVILY_API_KEY` | Web search for the research node |
| `ANTHROPIC_MODEL` | Optional. Defaults to `claude-opus-4-8`. |

## Real output

This isn't a canned example — it's an actual run against the live Claude and
Tavily APIs:

```
$ python main.py "Anthropic"

================================================================
ACCOUNT RESEARCH & OUTREACH PIPELINE — Anthropic
================================================================
Node timing breakdown:
  research_account      52.93s
  generate_outreach     11.02s
  sync_crm                0.31s
----------------------------------------------------------------
SUCCESS: Account processed in 64.28 seconds (Optimized from 45 minutes, ~42x faster)
CRM status: synced
================================================================
```

The research node correctly identified Anthropic's actual funding history,
real personas, and recent product moves — no hallucinated placeholder data:

```json
{
  "industry": "Artificial Intelligence / Frontier AI Research & Enterprise Software",
  "summary": "Anthropic is a leading AI safety company and maker of the Claude family of models... extraordinarily well-capitalized (recently raised $30B at a $380B valuation)...",
  "key_personas": [
    { "name": "Dario Amodei", "title": "CEO & Co-Founder", "relevance": "Economic buyer / executive sponsor for major strategic partnerships" },
    { "name": "Daniela Amodei", "title": "President & Co-Founder", "relevance": "Influential on operational tooling and commercial decisions" }
  ]
}
```

...and the generated outreach referenced that context directly instead of
using a generic template (full example in [`docs/example-output.md`](docs/example-output.md)).

## Model choice

Defaults to `claude-opus-4-8`. Since this pipeline's whole premise is speed,
`claude-sonnet-5` is a strong swap for latency-sensitive deployments — set
`ANTHROPIC_MODEL=claude-sonnet-5` — it holds near-Opus quality on
agentic/tool-calling work at lower per-token cost and latency. No code
changes needed either way.

## Project layout

| File | Purpose |
|---|---|
| `state.py` | `AgentState` TypedDict + execution metadata schema |
| `agents.py` | Node implementations, Tavily tool, structured-output schemas, mock CRM client, timing/error decorator |
| `graph.py` | `StateGraph` wiring: nodes, conditional edges, compilation |
| `main.py` | Entry point, checkpointer setup, benchmark timer and report |

## Reliability evals

`evals/` holds a task suite for
[agent-reliability-harness](https://github.com/djmoore-projects/agent-reliability-harness).
It runs the real graph (live Claude + Tavily) and grades every run on tool
use, final state, the CRM record actually written, outreach contract, grounding
(claim-level, against what the searches returned), cost, latency and steps.
Three tasks inject faults (a transient Tavily outage, a Claude failure inside
`generate_outreach`, Tavily down for the whole run).

```bash
pip install "agent-reliability-harness @ git+https://github.com/djmoore-projects/agent-reliability-harness"
agent-harness run evals/suite.yaml --out evals/results/candidate.json --trials 3 --repo-dir .
agent-harness compare evals/results/baseline.json evals/results/candidate.json --suite evals/suite.yaml
```

`.github/workflows/agent-eval.yml` runs it on PRs that touch the agent and fails
the check on regression (it skips cleanly when the API-key secrets aren't set).

**What the baseline found** (original code, [`evals/results/baseline.md`](evals/results/baseline.md)):
task success was **17%** (3 of 18 clean trials; 95% CI 6–39%). The run lost 15 of
its 33 trials to an exhausted API credit balance; the harness flags and excludes
those, so the baseline is partial. All 13 clean happy-path trials (7 real companies) failed:

| Failure | Trials hit | Cause |
|---|---|---|
| Outreach shipped with `[Name]` / `[Your Name]` placeholders | 13 / 13 | Nothing enforced "send-ready"; the prompt didn't forbid placeholders |
| More than 3 searches | 4 / 13 | The cap was on loop *iterations*, but Claude issues parallel tool calls per iteration |
| Research claims not supported by search results (<80% of claims grounded) | 3 / 14 | Model filled gaps from prior knowledge |
| Fictional company got a real company's execs, funding and news | 1 / 1 | Similarly named company in results, no entity check |
| An LLM blip in outreach re-ran all research: 8 searches, 108s, $0.41 vs ~$0.18 typical | 1 / 1 | Retry always restarted from `research_account` |

The fixes on this branch target exactly those: search *count* budget, resume
from the failed node, a code-enforced outreach contract with one repair pass,
and an entity-grounding instruction. The after-fix run is pending (it needs
API credit), so there are no "after" numbers here yet.

## Design notes

- **Retries resume at the failed node when its inputs are intact.** An
  outreach failure with research already in state retries `generate_outreach`
  only; anything else restarts from `research_account`, which every
  downstream step depends on. (Originally every retry restarted from research;
  the eval suite's `outreach-llm-blip` task showed that doubled cost and latency
  on a single transient error.)
- **Structured output over prompted JSON.** Both `research_account` and
  `generate_outreach` use `ChatAnthropic.with_structured_output(...)` against
  Pydantic schemas rather than asking the model to "return JSON" — this
  guarantees parseable, typed output instead of relying on prompt
  compliance.
- **Contracts in code, not just prompts.** Outreach length limits, channel
  order and "no placeholders" are checked by `outreach_violations()` after
  generation, with one targeted repair pass if the draft breaks them.
- **Bounded tool loop.** The research node caps tool-calling at 3 iterations
  *and* 3 total searches (Claude can request several searches in one turn), to
  keep latency and spend predictable.

## Contributing

Issues and PRs welcome. The codebase is intentionally small (4 files, no
hidden abstractions) — if you're extending it with a new node (e.g. a
`qualify_lead` scoring step, or a real HubSpot/Salesforce client instead of
the mock), the pattern to follow is `@timed_node` + a `dict` partial-state
return, wired into `graph.py` with a conditional edge for the failure case.

## License

[MIT](LICENSE)
