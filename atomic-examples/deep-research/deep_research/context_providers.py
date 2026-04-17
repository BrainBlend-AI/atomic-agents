"""
Context providers for the deep-research pipeline.

Context providers are how runtime state reaches an agent's system prompt.
Here we use one provider that renders the shared ``ResearchState`` (see
``state.py``) so the extractor, reflector, and writer all see a
consistent, up-to-date picture without having to plumb data through
their input schemas.

The planner and query agents deliberately don't use this provider — the
planner runs before any state exists, and the query agent only needs
what can fit cleanly into its input schema.
"""

from datetime import datetime

from atomic_agents.context import BaseDynamicContextProvider

from deep_research.state import ResearchState


class ResearchStateProvider(BaseDynamicContextProvider):
    """Renders the current plan, sources, and learnings for agents that need full context."""

    def __init__(self, title: str, state: ResearchState):
        super().__init__(title=title)
        self.state = state

    def get_info(self) -> str:
        if not self.state.sources and not self.state.learnings:
            return "No research has been done yet."

        lines: list[str] = []

        if self.state.sources:
            lines.append("### Sources")
            for s in self.state.sources:
                lines.append(f"[{s.id}] {s.title}")
                lines.append(f"      {s.url}")

        if self.state.learnings:
            lines.append("")
            lines.append("### Learnings so far (grouped by sub-topic)")
            seen_topics: list[str] = []
            for l in self.state.learnings:
                if l.sub_topic not in seen_topics:
                    seen_topics.append(l.sub_topic)
            for sub_topic in seen_topics:
                lines.append(f"**{sub_topic}**")
                for l in self.state.learnings_for(sub_topic):
                    lines.append(f"- {l.text} [{l.source_id}]")

        return "\n".join(lines)


class CurrentDateProvider(BaseDynamicContextProvider):
    """So agents don't get confused about what counts as 'recent'."""

    def __init__(self, title: str):
        super().__init__(title=title)

    def get_info(self) -> str:
        return datetime.utcnow().strftime("Today is %A, %B %d, %Y.")
