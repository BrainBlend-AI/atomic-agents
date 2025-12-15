# Orchestration and Multi-Agent Patterns

This guide covers patterns for building multi-agent systems and orchestrating complex workflows with Atomic Agents.

## Overview

Orchestration in Atomic Agents enables:

- **Tool Selection**: Agents that choose appropriate tools based on input
- **Multi-Agent Pipelines**: Chain agents for complex workflows
- **Dynamic Routing**: Route queries to specialized agents
- **Parallel Execution**: Run multiple agents concurrently
- **Agent Composition**: Combine agents for sophisticated behavior

## Tool Orchestration Pattern

The most common pattern: an orchestrator agent that selects and invokes tools.

```python
from typing import Union
import instructor
import openai
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator


# Define tool input schemas
class SearchToolInput(BaseIOSchema):
    """Input for web search tool."""
    queries: list[str] = Field(..., description="Search queries to execute")


class CalculatorToolInput(BaseIOSchema):
    """Input for calculator tool."""
    expression: str = Field(..., description="Mathematical expression to evaluate")


# Orchestrator output uses Union to select between tools
class OrchestratorOutput(BaseIOSchema):
    """Orchestrator decides which tool to use."""
    reasoning: str = Field(..., description="Why this tool was selected")
    tool_parameters: Union[SearchToolInput, CalculatorToolInput] = Field(
        ..., description="Parameters for the selected tool"
    )


class OrchestratorInput(BaseIOSchema):
    """User query for the orchestrator."""
    query: str = Field(..., description="User's question or request")


# Create the orchestrator agent
client = instructor.from_openai(openai.OpenAI())

orchestrator = AtomicAgent[OrchestratorInput, OrchestratorOutput](
    config=AgentConfig(
        client=client,
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an orchestrator that routes queries to appropriate tools.",
                "Use search for factual questions, current events, or lookups.",
                "Use calculator for mathematical expressions and computations."
            ],
            output_instructions=[
                "Analyze the query to determine the best tool.",
                "Provide clear reasoning for your choice.",
                "Format parameters correctly for the selected tool."
            ]
        )
    )
)


def process_query(query: str):
    """Process a query through the orchestrator."""
    result = orchestrator.run(OrchestratorInput(query=query))

    print(f"Reasoning: {result.reasoning}")

    # Route to appropriate tool based on output type
    if isinstance(result.tool_parameters, SearchToolInput):
        print(f"Using Search with queries: {result.tool_parameters.queries}")
        # search_results = search_tool.run(result.tool_parameters)
    elif isinstance(result.tool_parameters, CalculatorToolInput):
        print(f"Using Calculator with: {result.tool_parameters.expression}")
        # calc_result = calculator_tool.run(result.tool_parameters)


# Example usage
process_query("What is the capital of France?")  # Routes to search
process_query("Calculate 15% of 250")  # Routes to calculator
```

## Sequential Pipeline Pattern

Chain multiple agents where each agent's output feeds the next:

```python
from typing import List
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator


# Stage 1: Query Generation
class QueryGenInput(BaseIOSchema):
    topic: str = Field(..., description="Research topic")


class QueryGenOutput(BaseIOSchema):
    queries: List[str] = Field(..., description="Generated search queries")
    rationale: str = Field(..., description="Why these queries were chosen")


# Stage 2: Analysis
class AnalysisInput(BaseIOSchema):
    topic: str = Field(..., description="Original topic")
    search_results: str = Field(..., description="Aggregated search results")


class AnalysisOutput(BaseIOSchema):
    summary: str = Field(..., description="Synthesized summary")
    key_points: List[str] = Field(..., description="Key findings")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class ResearchPipeline:
    """Multi-stage research pipeline."""

    def __init__(self, client):
        # Query generation agent
        self.query_agent = AtomicAgent[QueryGenInput, QueryGenOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=["Generate effective search queries for research."],
                    steps=[
                        "Analyze the topic for key concepts.",
                        "Generate 3-5 diverse, specific queries.",
                        "Cover different aspects of the topic."
                    ]
                )
            )
        )

        # Analysis agent
        self.analysis_agent = AtomicAgent[AnalysisInput, AnalysisOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=["Synthesize research into clear summaries."],
                    steps=[
                        "Review all search results.",
                        "Identify patterns and key information.",
                        "Generate a comprehensive summary."
                    ]
                )
            )
        )

    def research(self, topic: str, search_function) -> AnalysisOutput:
        """Execute the full research pipeline."""

        # Stage 1: Generate queries
        query_result = self.query_agent.run(QueryGenInput(topic=topic))
        print(f"Generated {len(query_result.queries)} queries")

        # Stage 2: Execute searches (external function)
        all_results = []
        for query in query_result.queries:
            results = search_function(query)
            all_results.append(f"Query: {query}\nResults: {results}")

        combined_results = "\n\n".join(all_results)

        # Stage 3: Analyze results
        analysis = self.analysis_agent.run(AnalysisInput(
            topic=topic,
            search_results=combined_results
        ))

        return analysis


# Usage
def mock_search(query: str) -> str:
    return f"[Simulated results for: {query}]"

pipeline = ResearchPipeline(client)
result = pipeline.research("renewable energy benefits", mock_search)
print(f"Summary: {result.summary}")
print(f"Confidence: {result.confidence:.0%}")
```

## Parallel Execution Pattern

Run multiple agents concurrently for independent tasks:

```python
import asyncio
from typing import List
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator


class AnalysisRequest(BaseIOSchema):
    text: str = Field(..., description="Text to analyze")


class SentimentOutput(BaseIOSchema):
    sentiment: str = Field(..., description="positive, negative, or neutral")
    confidence: float = Field(..., ge=0.0, le=1.0)


class TopicOutput(BaseIOSchema):
    topics: List[str] = Field(..., description="Identified topics")
    primary_topic: str = Field(..., description="Main topic")


class SummaryOutput(BaseIOSchema):
    summary: str = Field(..., description="Brief summary")
    word_count: int = Field(..., description="Original word count")


class ParallelAnalyzer:
    """Runs multiple analysis agents in parallel."""

    def __init__(self, async_client):
        self.sentiment_agent = AtomicAgent[AnalysisRequest, SentimentOutput](
            config=AgentConfig(
                client=async_client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=["Analyze sentiment of text."]
                )
            )
        )

        self.topic_agent = AtomicAgent[AnalysisRequest, TopicOutput](
            config=AgentConfig(
                client=async_client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=["Extract topics from text."]
                )
            )
        )

        self.summary_agent = AtomicAgent[AnalysisRequest, SummaryOutput](
            config=AgentConfig(
                client=async_client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=["Summarize text concisely."]
                )
            )
        )

    async def analyze(self, text: str) -> dict:
        """Run all analyses in parallel."""
        request = AnalysisRequest(text=text)

        # Run all agents concurrently
        sentiment_task = self.sentiment_agent.run_async(request)
        topic_task = self.topic_agent.run_async(request)
        summary_task = self.summary_agent.run_async(request)

        # Wait for all to complete
        sentiment, topics, summary = await asyncio.gather(
            sentiment_task,
            topic_task,
            summary_task
        )

        return {
            "sentiment": sentiment,
            "topics": topics,
            "summary": summary
        }


# Usage
async def main():
    from openai import AsyncOpenAI

    async_client = instructor.from_openai(AsyncOpenAI())
    analyzer = ParallelAnalyzer(async_client)

    text = "The new renewable energy policy has shown promising results..."
    results = await analyzer.analyze(text)

    print(f"Sentiment: {results['sentiment'].sentiment}")
    print(f"Topics: {results['topics'].topics}")
    print(f"Summary: {results['summary'].summary}")


asyncio.run(main())
```

## Router Pattern

Route queries to specialized agents based on classification:

```python
from typing import Literal
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator


class RouterInput(BaseIOSchema):
    query: str = Field(..., description="User query to route")


class RouterOutput(BaseIOSchema):
    category: Literal["technical", "creative", "analytical", "general"] = Field(
        ..., description="Query category"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Why this category was chosen")


class QueryResponse(BaseIOSchema):
    response: str = Field(..., description="Response to the query")


class AgentRouter:
    """Routes queries to specialized agents."""

    def __init__(self, client):
        # Router agent classifies queries
        self.router = AtomicAgent[RouterInput, RouterOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "Classify queries into categories:",
                        "- technical: coding, engineering, technical problems",
                        "- creative: writing, art, brainstorming",
                        "- analytical: data analysis, research, comparisons",
                        "- general: other queries"
                    ]
                )
            )
        )

        # Specialized agents for each category
        self.agents = {
            "technical": self._create_agent(client, [
                "You are a technical expert.",
                "Provide detailed, accurate technical answers.",
                "Include code examples when appropriate."
            ]),
            "creative": self._create_agent(client, [
                "You are a creative assistant.",
                "Think outside the box.",
                "Offer imaginative and original ideas."
            ]),
            "analytical": self._create_agent(client, [
                "You are an analytical expert.",
                "Provide data-driven insights.",
                "Structure analysis logically."
            ]),
            "general": self._create_agent(client, [
                "You are a helpful general assistant.",
                "Provide clear, helpful responses."
            ])
        }

    def _create_agent(self, client, background: list) -> AtomicAgent:
        return AtomicAgent[RouterInput, QueryResponse](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(background=background)
            )
        )

    def route_and_respond(self, query: str) -> tuple[str, QueryResponse]:
        """Route query to appropriate agent and get response."""
        # Classify the query
        routing = self.router.run(RouterInput(query=query))
        print(f"Routed to: {routing.category} ({routing.confidence:.0%} confidence)")

        # Get response from specialized agent
        agent = self.agents[routing.category]
        response = agent.run(RouterInput(query=query))

        return routing.category, response


# Usage
router = AgentRouter(client)
category, response = router.route_and_respond("How do I implement a binary search tree?")
print(f"Category: {category}")
print(f"Response: {response.response}")
```

## Context Sharing Between Agents

Share information between agents using context providers:

```python
from typing import List
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator, BaseDynamicContextProvider


class SharedKnowledgeProvider(BaseDynamicContextProvider):
    """Shares knowledge between agents."""

    def __init__(self):
        super().__init__(title="Shared Knowledge")
        self.facts: List[str] = []
        self.decisions: List[str] = []

    def add_fact(self, fact: str):
        self.facts.append(fact)

    def add_decision(self, decision: str):
        self.decisions.append(decision)

    def get_info(self) -> str:
        output = []
        if self.facts:
            output.append("Known Facts:")
            output.extend(f"  - {f}" for f in self.facts)
        if self.decisions:
            output.append("Previous Decisions:")
            output.extend(f"  - {d}" for d in self.decisions)
        return "\n".join(output) if output else "No shared knowledge yet."


class FactInput(BaseIOSchema):
    query: str = Field(..., description="Query to process")


class FactOutput(BaseIOSchema):
    facts: List[str] = Field(..., description="Extracted facts")
    has_new_info: bool = Field(..., description="Whether new facts were found")


class DecisionInput(BaseIOSchema):
    question: str = Field(..., description="Decision to make")


class DecisionOutput(BaseIOSchema):
    decision: str = Field(..., description="The decision made")
    reasoning: str = Field(..., description="Reasoning behind decision")


class CollaborativeAgents:
    """Agents that share context and build on each other's work."""

    def __init__(self, client):
        self.shared_knowledge = SharedKnowledgeProvider()

        # Fact extraction agent
        self.fact_agent = AtomicAgent[FactInput, FactOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=["Extract factual information from queries."]
                )
            )
        )
        self.fact_agent.register_context_provider("knowledge", self.shared_knowledge)

        # Decision-making agent
        self.decision_agent = AtomicAgent[DecisionInput, DecisionOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "Make decisions based on available facts.",
                        "Reference the shared knowledge when reasoning."
                    ]
                )
            )
        )
        self.decision_agent.register_context_provider("knowledge", self.shared_knowledge)

    def process_information(self, text: str):
        """Extract facts and add to shared knowledge."""
        result = self.fact_agent.run(FactInput(query=text))
        for fact in result.facts:
            self.shared_knowledge.add_fact(fact)
        return result

    def make_decision(self, question: str):
        """Make decision using shared knowledge."""
        result = self.decision_agent.run(DecisionInput(question=question))
        self.shared_knowledge.add_decision(f"{question} -> {result.decision}")
        return result


# Usage
collab = CollaborativeAgents(client)

# First agent extracts facts
collab.process_information("Solar panels have 20-25 year lifespans and costs dropped 89% since 2010.")
collab.process_information("Wind energy now provides 10% of global electricity.")

# Second agent makes decisions using accumulated knowledge
decision = collab.make_decision("Should we invest in renewable energy?")
print(f"Decision: {decision.decision}")
print(f"Reasoning: {decision.reasoning}")
```

## Supervisor Pattern

A supervisor agent that manages and validates worker agents:

```python
from typing import List, Optional
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator


class TaskAssignment(BaseIOSchema):
    task: str = Field(..., description="Task to complete")


class WorkerOutput(BaseIOSchema):
    result: str = Field(..., description="Task result")
    confidence: float = Field(..., ge=0.0, le=1.0)


class SupervisorReview(BaseIOSchema):
    task: str = Field(..., description="Original task")
    worker_result: str = Field(..., description="Worker's result")


class SupervisorOutput(BaseIOSchema):
    approved: bool = Field(..., description="Whether result is approved")
    feedback: Optional[str] = Field(None, description="Feedback if not approved")
    final_result: str = Field(..., description="Final result (possibly refined)")


class SupervisedWorkflow:
    """Workflow with supervisor validation."""

    def __init__(self, client, max_iterations: int = 3):
        self.max_iterations = max_iterations

        # Worker agent
        self.worker = AtomicAgent[TaskAssignment, WorkerOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=["Complete assigned tasks thoroughly."]
                )
            )
        )

        # Supervisor agent
        self.supervisor = AtomicAgent[SupervisorReview, SupervisorOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "Review worker outputs for quality.",
                        "Approve good work, provide feedback for improvements.",
                        "Refine results if needed."
                    ]
                )
            )
        )

    def execute(self, task: str) -> SupervisorOutput:
        """Execute task with supervisor review loop."""

        for iteration in range(self.max_iterations):
            # Worker attempts task
            worker_result = self.worker.run(TaskAssignment(task=task))
            print(f"Iteration {iteration + 1}: Worker confidence {worker_result.confidence:.0%}")

            # Supervisor reviews
            review = self.supervisor.run(SupervisorReview(
                task=task,
                worker_result=worker_result.result
            ))

            if review.approved:
                print("Supervisor approved result")
                return review
            else:
                print(f"Supervisor feedback: {review.feedback}")
                # Update task with feedback for next iteration
                task = f"{task}\n\nPrevious attempt feedback: {review.feedback}"

        print("Max iterations reached, returning best effort")
        return review


# Usage
workflow = SupervisedWorkflow(client)
result = workflow.execute("Write a haiku about programming")
print(f"Final result: {result.final_result}")
```

## Best Practices

### 1. Design Clear Interfaces

Define explicit input/output schemas for each agent:

```python
# Good: Clear, typed interfaces
class AgentAOutput(BaseIOSchema):
    data: str
    metadata: dict

class AgentBInput(BaseIOSchema):
    data: str  # Explicitly matches AgentAOutput.data
```

### 2. Handle Failures Gracefully

Implement fallbacks and error handling:

```python
def execute_with_fallback(primary_agent, fallback_agent, input_data):
    try:
        return primary_agent.run(input_data)
    except Exception as e:
        print(f"Primary failed: {e}, using fallback")
        return fallback_agent.run(input_data)
```

### 3. Monitor Agent Interactions

Log inter-agent communication:

```python
def logged_handoff(from_agent: str, to_agent: str, data):
    print(f"[{from_agent}] -> [{to_agent}]: {type(data).__name__}")
    return data
```

### 4. Keep Agents Focused

Each agent should have a single responsibility:

```python
# Good: Single responsibility
query_generator = AtomicAgent[...]  # Only generates queries
analyzer = AtomicAgent[...]  # Only analyzes

# Avoid: Multiple responsibilities in one agent
do_everything_agent = AtomicAgent[...]  # Too complex
```

## Summary

| Pattern | Use Case | Key Benefit |
|---------|----------|-------------|
| Tool Orchestration | Dynamic tool selection | Flexible routing |
| Sequential Pipeline | Multi-step processing | Clear data flow |
| Parallel Execution | Independent analyses | Performance |
| Router Pattern | Query classification | Specialization |
| Context Sharing | Knowledge accumulation | Collaboration |
| Supervisor Pattern | Quality assurance | Validation |

Choose patterns based on your workflow requirements and combine them for sophisticated agent systems.
