# Deep Research Agent

A didactic example of a proper deep-research pipeline built out of small, single-purpose Atomic Agents.

Unlike a typical "search-and-summarise" agent — generate one set of queries, fetch results, write an answer — this example iterates: it plans sub-topics, researches each one across multiple depth levels, reflects on whether each has enough coverage, and produces a report where every claim is tied to a registered source.

## Pipeline

1. **Plan.** A `PlannerAgent` breaks the question into 3–5 durable sub-topics, each seeded with a handful of queries.
2. **Research** (per sub-topic, up to N iterations):
   - Search (SearXNG) and scrape the top new URLs.
   - `ExtractorAgent` pulls atomic, citable claims from each scraped page.
   - `ReflectorAgent` decides whether the sub-topic has enough material, or emits follow-up queries for the next iteration.
3. **Write.** `WriterAgent` drafts a cited report from the accumulated state, then runs a second pass over its own draft to strip any sentence whose citation doesn't correspond to a real source.

Every agent has a single responsibility and reads / contributes to a shared `ResearchState` object. The loop itself lives in `main.py` as plain Python — no megagent, no hidden control flow.

## Getting Started

1. **Clone the main Atomic Agents repository:**
   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. **Navigate to the Deep Research directory:**
   ```bash
   cd atomic-agents/atomic-examples/deep-research
   ```

3. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

4. **Set up environment variables:**
   Create a `.env` file in the `deep-research` directory with:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   SEARXNG_BASE_URL=http://localhost:8080
   SEARXNG_API_KEY=your_searxng_secret_key
   ```

5. **Set up SearXNG:**
   - Install from the [official repository](https://github.com/searxng/searxng).
   - Default configuration expects SearXNG at `http://localhost:8080`.
   - JSON output must be enabled in `settings.yml` (look for the `formats:` key).

6. **Run a research query:**
   ```bash
   uv run python -m deep_research "What is the current state of fusion energy research?"
   ```

## File Layout

```
deep_research/
├── config.py              # Model + connectivity + research budgets
├── state.py               # ResearchState dataclass — the one source of truth
├── context_providers.py   # Renders state into agent system prompts
├── agents/
│   ├── planner_agent.py    # Question → sub-topics (with initial queries)
│   ├── extractor_agent.py  # One scraped source → atomic claims
│   ├── reflector_agent.py  # Sub-topic state → sufficient? + next queries
│   └── writer_agent.py     # Full state → cited report (draft + verify passes)
├── tools/
│   ├── searxng_search.py
│   └── webpage_scraper.py
└── main.py                 # Plain orchestrator: plan → research → write
```

## Budgets

All limits live in `ResearchBudget` inside `config.py`. Tune to taste:

| Knob | Default | Meaning |
|---|---|---|
| `num_sub_topics` | 4 | Plan width |
| `max_depth_per_sub_topic` | 2 | Max iterations per sub-topic; reflector can stop earlier |
| `search_results_per_query` | 5 | SearXNG page size |
| `scrape_top_n_per_iteration` | 3 | New URLs scraped per iteration |
| `hard_call_cap` | 80 | Global safety net on total agent calls |

Worst-case run: roughly 50 agent calls and 24 scrapes.

## License

MIT — see the [LICENSE](../../LICENSE) file.
