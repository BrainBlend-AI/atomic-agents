"""
Deep-research orchestrator.

Reads like a recipe: plan → (per sub-topic) search → scrape → extract →
reflect → (maybe loop) → write. Each step is a call to a single-purpose
agent (see ``deep_research/agents/``) that reads from and contributes to
the shared ``ResearchState`` (see ``state.py``).

Run:  ``python -m deep_research "your question here"``
"""

import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from deep_research.agents.extractor_agent import ExtractorInput, extractor_agent
from deep_research.agents.planner_agent import PlannerInput, planner_agent
from deep_research.agents.reflector_agent import ReflectorInput, reflector_agent
from deep_research.agents.writer_agent import WriterInput, writer_agent
from deep_research.config import ChatConfig, ResearchBudget
from deep_research.context_providers import CurrentDateProvider, ResearchStateProvider
from deep_research.state import Learning, ResearchState, SubTopic
from deep_research.tools.searxng_search import (
    SearXNGSearchTool,
    SearXNGSearchToolConfig,
    SearXNGSearchToolInputSchema,
)
from deep_research.tools.webpage_scraper import (
    WebpageScraperTool,
    WebpageScraperToolInputSchema,
)

console = Console()


def wire_context_providers(state: ResearchState) -> None:
    """Register the state + current-date providers on every agent that needs them.

    The planner is the only agent that runs before any state exists, so
    it gets only the date. All others see the live ``ResearchState``.
    """
    state_provider = ResearchStateProvider("Research State", state)
    date_provider = CurrentDateProvider("Current Date")

    planner_agent.register_context_provider("current_date", date_provider)

    for agent in (extractor_agent, reflector_agent, writer_agent):
        agent.register_context_provider("current_date", date_provider)
        agent.register_context_provider("research_state", state_provider)


def plan_research(state: ResearchState) -> None:
    """Run the planner once to fill in ``state.plan``."""
    console.rule("[bold cyan]1. Plan")
    result = planner_agent.run(
        PlannerInput(question=state.question, num_sub_topics=ResearchBudget.num_sub_topics)
    )
    state.agent_calls += 1

    for st in result.sub_topics:
        state.plan.append(SubTopic(name=st.name, initial_queries=list(st.initial_queries)))
        state.queries_seen.update(st.initial_queries)

    for i, st in enumerate(state.plan, 1):
        console.print(f"  [bold]{i}. {st.name}[/bold]")
        for q in st.initial_queries:
            console.print(f"     • [dim]{q}[/dim]")


def search_and_scrape(
    queries: list[str],
    state: ResearchState,
    search: SearXNGSearchTool,
    scraper: WebpageScraperTool,
) -> list[tuple[str, str]]:
    """Run SearXNG on the given queries, scrape the top N new URLs, return ``[(source_id, content), …]``.

    Skips URLs we've already scraped in a previous iteration. Registers
    every new URL as a ``Source`` so downstream claims can cite by ID.
    """
    results = search.run(
        SearXNGSearchToolInputSchema(queries=queries, category="general")
    )

    scraped: list[tuple[str, str]] = []
    for r in results.results:
        if r.url in state.urls_seen:
            continue
        if len(scraped) >= ResearchBudget.scrape_top_n_per_iteration:
            break

        page = scraper.run(WebpageScraperToolInputSchema(url=r.url, include_links=False))
        if page.error or not page.content.strip():
            continue

        source = state.register_source(url=r.url, title=r.title or page.metadata.title)
        scraped.append((source.id, page.content))

    return scraped


def extract_claims(sub_topic: SubTopic, scraped: list[tuple[str, str]], state: ResearchState) -> int:
    """Call the extractor once per scraped source, append claims to state, return claim count."""
    new_claim_count = 0
    for source_id, content in scraped:
        source = next(s for s in state.sources if s.id == source_id)
        result = extractor_agent.run(
            ExtractorInput(
                sub_topic=sub_topic.name,
                source_url=source.url,
                source_title=source.title,
                content=content[: ResearchBudget.max_extractor_content_chars],
            )
        )
        state.agent_calls += 1

        for claim in result.claims:
            state.learnings.append(
                Learning(text=claim, source_id=source_id, sub_topic=sub_topic.name)
            )
            new_claim_count += 1
    return new_claim_count


def reflect(sub_topic: SubTopic, iteration: int, state: ResearchState) -> tuple[bool, list[str]]:
    """Ask the reflector whether this sub-topic has enough material. Returns (sufficient, next_queries)."""
    result = reflector_agent.run(
        ReflectorInput(
            sub_topic=sub_topic.name,
            iterations_so_far=iteration,
            max_iterations=ResearchBudget.max_depth_per_sub_topic,
        )
    )
    state.agent_calls += 1

    console.print(f"    [italic]{result.reasoning}[/italic]")

    # Dedup: reflector might suggest a query we've already tried.
    fresh = [q for q in result.next_queries if q not in state.queries_seen]
    state.queries_seen.update(fresh)
    return result.sufficient, fresh


def research_sub_topic(
    sub_topic: SubTopic,
    state: ResearchState,
    search: SearXNGSearchTool,
    scraper: WebpageScraperTool,
) -> None:
    """Run the depth loop for a single sub-topic until sufficient or out of iterations."""
    console.rule(f"[bold cyan]Sub-topic: {sub_topic.name}")

    queries = sub_topic.initial_queries
    for iteration in range(1, ResearchBudget.max_depth_per_sub_topic + 1):
        if state.agent_calls >= ResearchBudget.hard_call_cap:
            console.print("[red]Hit hard call cap — stopping this sub-topic.[/red]")
            return

        console.print(f"\n  [bold]Iteration {iteration}/{ResearchBudget.max_depth_per_sub_topic}[/bold]")
        console.print(f"    queries: {queries}")

        scraped = search_and_scrape(queries, state, search, scraper)
        console.print(f"    scraped {len(scraped)} new source(s)")

        if not scraped:
            # No new information to extract from — further iterations won't help either.
            sub_topic.sufficient = True
            return

        new_claims = extract_claims(sub_topic, scraped, state)
        console.print(f"    extracted {new_claims} claim(s)")

        sufficient, next_queries = reflect(sub_topic, iteration, state)
        if sufficient or iteration == ResearchBudget.max_depth_per_sub_topic or not next_queries:
            sub_topic.sufficient = sufficient
            return

        queries = next_queries


def write_report(state: ResearchState) -> tuple[str, str]:
    """Draft the report, then run a cheap verification pass over it. Returns (headline, report)."""
    console.rule("[bold cyan]3. Write")

    draft = writer_agent.run(
        WriterInput(question=state.question, mode="draft", draft="")
    )
    state.agent_calls += 1
    console.print("  [dim]draft written, verifying citations…[/dim]")

    verified = writer_agent.run(
        WriterInput(question=state.question, mode="verify", draft=draft.report)
    )
    state.agent_calls += 1
    return verified.headline, verified.report


def run(question: str) -> None:
    """Top-level pipeline. Reads like an outline of what 'deep research' means in this project."""
    console.print(Panel.fit(
        f"[bold]Deep Research[/bold]\n{question}",
        border_style="blue",
    ))

    state = ResearchState(question=question)
    wire_context_providers(state)

    search = SearXNGSearchTool(
        SearXNGSearchToolConfig(
            base_url=ChatConfig.searxng_base_url,
            max_results=ResearchBudget.search_results_per_query,
        )
    )
    scraper = WebpageScraperTool()

    plan_research(state)

    console.rule("[bold cyan]2. Research")
    for sub_topic in state.plan:
        research_sub_topic(sub_topic, state, search, scraper)

    headline, report = write_report(state)

    console.rule("[bold green]Report")
    console.print(Panel(f"[bold]{headline}[/bold]", border_style="green"))
    console.print(Markdown(report))

    console.print(
        f"\n[dim]Stats: {state.agent_calls} agent calls, {len(state.sources)} sources, "
        f"{len(state.learnings)} learnings.[/dim]"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        console.print("[red]Usage:[/red] python -m deep_research \"your question\"")
        sys.exit(1)
    run(" ".join(args))
