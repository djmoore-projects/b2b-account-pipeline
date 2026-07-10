# Example output

Captured from a real run — `python main.py "Anthropic"` — against the live
Claude and Tavily APIs. Nothing below is hand-edited or a placeholder.

## Console report

```
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

## Structured research (`state["research_data"]`)

```json
{
  "company_name": "Anthropic",
  "industry": "Artificial Intelligence / Frontier AI Research & Enterprise Software",
  "summary": "Anthropic is a leading AI safety company and maker of the Claude family of models, founded by ex-OpenAI siblings Dario and Daniela Amodei and backed by Amazon and Google. It's extraordinarily well-capitalized (recently raised $30B at a $380B valuation) and pivoting aggressively from chatbots to enterprise/agentic AI with products like Claude Code, Cowork, and an enterprise agents program. As a hyper-scaling, elite engineering org, it has a strong build-vs-buy bias and is both a potential buyer and an increasingly aggressive competitor to enterprise SaaS.",
  "key_personas": [
    {
      "name": "Mike Krieger",
      "title": "Former Chief Product Officer (now co-leading Anthropic Labs)",
      "relevance": "Owns product engineering, PM, and design behind enterprise app expansion; recently reshuffled to Labs, so verify current CPO — key champion/technical buyer"
    },
    {
      "name": "Dario Amodei",
      "title": "CEO & Co-Founder",
      "relevance": "Sets strategic vision and mission; economic buyer / executive sponsor for major strategic partnerships"
    },
    {
      "name": "Daniela Amodei",
      "title": "President & Co-Founder",
      "relevance": "Oversees operations, people, and go-to-market scaling; influential on operational tooling and commercial decisions"
    }
  ]
}
```

## Generated outreach (`state["outreach_sequence"]`)

**Step 1 — email**

> **Subject:** Scaling Labs headcount after the $30B raise
>
> Hi Mike,
>
> Congrats on the move to co-lead Anthropic Labs — going from CPO to standing
> up an incubator right after a $30B Series G is no small pivot.
>
> With Claude Code hitting $1B+ in six months and Cowork + the enterprise
> agents program launching back-to-back, I imagine Labs is spinning up teams
> fast. That kind of 0-to-1 velocity usually strains the operational glue
> between PM, eng, and design.
>
> We help elite eng orgs (with a strong build-vs-buy bias) keep that
> connective tissue lightweight so builders stay building. Worth a 15-min
> look at how we'd fit alongside what you'd rather build in-house?
>
> Best,
> [Your Name]

**Step 2 — LinkedIn connection request**

> Hi Mike — following your shift from CPO to co-leading Anthropic Labs.
> Standing up an incubator right after the $30B raise, on the heels of
> Cowork and the enterprise agents launch, is a fascinating 0-to-1
> challenge. Would love to connect and swap notes on scaling new product
> teams.

**Step 3 — follow-up email**

> **Subject:** Re: Scaling Labs headcount after the $30B raise
>
> Hi Mike,
>
> Quick follow-up. Given how quickly MCP became a ~100M-download standard,
> I'd guess Labs is prioritizing where to build vs. buy across its new bets.
>
> If it's useful, I can send a one-pager on how similar hyper-scaling orgs
> decided what to keep in-house versus offload during that first 0-to-1
> sprint — no meeting required.
>
> Want me to send it over?
>
> Best,
> [Your Name]

## CRM sync payload

```json
{
  "id": "crm_cf037d776b",
  "synced_at": "2026-07-10T16:28:03.487732+00:00",
  "company_name": "Anthropic",
  "industry": "Artificial Intelligence / Frontier AI Research & Enterprise Software"
}
```
