# Agent reliability report — `b2b-account-pipeline` / `baseline`

- Generated 2026-10-04T17:50:07+00:00 · git `4ba025c` · 11 tasks × 3 trial(s) = 18 runs

| Metric | Value |
|---|---|
| Task success (pass@1) | **17%** (95% CI 6%–39%) |
| Passed every trial (pass^3) | 18% |
| Tool-use checks passed | 86% |
| Final-state checks passed | 92% |
| Quality (judge) checks passed | 79% |
| Budget checks passed | 100% |
| Mean cost / task | $0.1791 (judge: $1.20 total) |
| Latency p50 / p95 | 54.5s / 70.2s |
| Mean steps | 8.1 (4.5 LLM, 3.6 tool) |

⚠️ **15 trial(s) excluded** for provider/infrastructure errors (auth, billing, quota). They say nothing about the agent; re-run before trusting these numbers.

## Most common failing checks

| Check | Failures |
|---|---|
| `no-template-placeholders` | 13 |
| `search-count` | 4 |
| `research-grounded` | 3 |
| `outreach-personalized` | 2 |
| `admits-uncertainty` | 1 |
| `personas-1-to-3` | 1 |
| `no-redundant-research` | 1 |
| `research-runs-once` | 1 |

## Per task

| Task | Passed | Mean cost | Mean latency | Mean steps |
|---|---|---|---|---|
| `datadog` | 0/2 | $0.1666 | 51.0s | 7.0 |
| `fictional-company` | 0/1 | $0.1582 | 49.1s | 7.0 |
| `figma` | 0/2 | $0.1701 | 54.2s | 7.0 |
| `hightouch` | 0/2 | $0.2069 | 58.0s | 9.0 |
| `outreach-llm-blip` | 0/1 | $0.4106 | 108.3s | 17.0 |
| `rippling` | 0/2 | $0.1651 | 53.9s | 7.0 |
| `search-hard-down` | 2/2 | $0.0486 | 8.8s | 6.0 |
| `search-outage-recovers` | 1/1 | $0.2249 | 61.5s | 11.0 |
| `snowflake` | 0/2 | $0.1933 | 59.0s | 8.0 |
| `stripe` | 0/2 | $0.1621 | 56.3s | 7.0 |
| `vanta` | 0/1 | $0.2044 | 63.4s | 9.0 |

## Failure details

### `datadog` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 96w/595c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 56w/362c)

### `datadog` trial 1 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 99w/615c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 64w/384c)

### `fictional-company` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **admits-uncertainty** (quality): The output names specific executives, a funding amount, investors, and news items, and presents them as fact. These are attributed to a different, similarly named company ('Quillon'). A caveat says no results exist for 'Quillon Dynamics Ltd', but the research data still asserts these specifics prominently in the structured fields (company_name, recent_funding, key_personas). It does not signal that little or no reliable information was found; it fills every field with specifics. The rubric requires no named executives, funding or news attributed to the company, so this fails.

### `figma` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **personas-1-to-3** (state): failed max_len=3; value=[{"name": "Dylan Field", "title": "CEO, President & Co-founder (Chairman)", "relevance": "Top strategic decision-maker a…
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 103w/615c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 74w/408c)
- ❌ **research-grounded** (quality): 19/24 claims supported; unsupported: ['Figma went public in mid-2025', "Adobe's proposed $20B acquisition was abandoned in late 2023 due to regulatory pressure", 'Figma Make is prompt-to-app', 'Figma Sites is design-to-website, Buzz is marketing assets, Draw is illustration']

### `figma` trial 1 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 97w/611c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 70w/413c)

### `hightouch` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **search-count** (tool_use): web_search called 4x, expected [1, 3]
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 103w/661c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 75w/465c)
- ❌ **research-grounded** (quality): 17/25 claims supported; unsupported: ['The $80M Series C occurred in early 2025', 'The July 2023 Series C was at a ~$615M valuation', 'The July 2023 Series C involved Bain Capital Ventures, ICONIQ Growth, and Databricks Ventures', "Hightouch's ARR was ~$20M a couple years prior"]
- ❌ **outreach-personalized** (quality): (1) Met: the first email cites concrete facts from the research data, including ~$100M ARR, the Snowflake Ventures + Capital One Ventures investment, AI Decisioning and the NYC office. (3) Met: every message is aimed at Josh Kanagy, the CRO persona. (2) Not cleanly met. Step 3 lists Spotify, Warner Music and PetSmart in parentheses as examples of Hightouch's Fortune 500 accounts. The research data names them only as customers, not as Fortune 500 companies, and Spotify and PetSmart are not Fortune 500 companies. Step 1 says the investment happened "this summer", but the data dates it to July 2025 and places the ARR news in April 2026, so the timing claim is unsupported and internally inconsistent. Step 1 also states as fact that the repositioning is "clearly" landing with enterprise buyers, an inference the data does not establish. Under strict grading these unsupported claims fail criterion 2.

### `hightouch` trial 1 — path: research_account → generate_outreach → sync_crm
- ❌ **search-count** (tool_use): web_search called 4x, expected [1, 3]
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 89w/553c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 68w/409c)

### `outreach-llm-blip` trial 0 — path: research_account → generate_outreach → handle_error → research_account → generate_outreach → sync_crm
- ❌ **no-redundant-research** (tool_use): web_search called 8x, expected [0, 3]
- ❌ **research-runs-once** (tool_use): research_account → generate_outreach → handle_error → research_account → generate_outreach → sync_crm

### `rippling` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 112w/652c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 79w/436c)

### `rippling` trial 1 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 104w/618c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 72w/426c)

### `snowflake` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 100w/602c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 65w/372c)

### `snowflake` trial 1 — path: research_account → generate_outreach → sync_crm
- ❌ **search-count** (tool_use): web_search called 4x, expected [1, 3]
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 93w/563c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 63w/390c)
- ❌ **outreach-personalized** (quality): (1) Met: the first email cites concrete researched facts, namely the CFO appointment in September, the move from GitLab, ~29% growth to $4.68B, the ~$200M Anthropic partnership and the $7B+ AWS marketplace figure.
(3) Met: all three messages are aimed at Brian Robins, a listed persona.
(2) Not met: the research describes $7B+ as lifetime AWS marketplace *sales*, which is revenue flowing to Snowflake. The email instead calls the Anthropic and AWS figures "commitments scaling fast" and treats them as "that tooling spend" whose ROI the CFO should track. That claims Snowflake is spending $7B+ on AWS tooling, which the research data does not support. It is a material factual distortion, so the strict standard is not met.

### `stripe` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 97w/595c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 79w/459c)
- ❌ **research-grounded** (quality): 18/23 claims supported; unsupported: ['Recent raises are liquidity tender offers rather than primary capital', 'Stripe added multi-currency money management to the Dashboard (store/convert currencies, local rails, virtual/physical cards) for US & UK businesses', 'Stripe offers APIs for payments, billing, treasury, lending, and card issuing', 'Stripe remains privately held']

### `stripe` trial 1 — path: research_account → generate_outreach → sync_crm
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 97w/645c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 73w/491c)

### `vanta` trial 0 — path: research_account → generate_outreach → sync_crm
- ❌ **search-count** (tool_use): web_search called 4x, expected [1, 3]
- ❌ **no-template-placeholders** (state): 1/3 ok; #0 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 100w/600c); #2 not_matches="\\[(first ?name|name|your name|company|title)\\]|\\{\\{" (got 68w/394c)
