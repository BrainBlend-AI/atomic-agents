import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase

from web_search_agent.tools.searxng_search import (
    SearxNGSearchTool,
    SearxNGSearchToolConfig,
    SearxNGSearchToolInputSchema,
)

from web_search_agent.agents.query_agent import QueryAgentInputSchema, query_agent
from web_search_agent.agents.question_answering_agent import question_answering_agent, QuestionAnsweringAgentInputSchema

import openai
import instructor

load_dotenv()

# Initialize a Rich Console for pretty console outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Initialize the SearxNGSearchTool
search_tool = SearxNGSearchTool(config=SearxNGSearchToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=5))

# Initialize the BaseAgent
agent = BaseAgent(
    config=BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))),
        model="gpt-4o-mini",
        memory=memory,
    )
)

# Example usage
instruction = "Tell me about the Atomic Agents AI agent framework."
num_queries = 3

# Generate queries using the query agent
query_input = QueryAgentInputSchema(instruction=instruction, num_queries=num_queries)
generated_queries = query_agent.run(query_input)

console.print("[bold blue]Generated Queries:[/bold blue]")
for query in generated_queries.queries:
    console.print(f"- {query}")

# Perform searches using the generated queries
search_input = SearxNGSearchToolInputSchema(queries=generated_queries.queries, category="general")


class SearchResultsProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.search_results = []

    def get_info(self) -> str:
        return f"SEARCH RESULTS: {self.search_results}"


try:
    search_results = search_tool.run(search_input)
    search_results_provider = SearchResultsProvider(title="Search Results")
    search_results_provider.search_results = search_results

    question_answering_agent.register_context_provider("search results", search_results_provider)

    answer = question_answering_agent.run(QuestionAnsweringAgentInputSchema(question=instruction))

    # Create a Rich Console instance
    console = Console()

    # Print the answer using Rich's Markdown rendering
    console.print("\n[bold blue]Answer:[/bold blue]")
    console.print(Markdown(answer.markdown_output))

    # Print references
    console.print("\n[bold blue]References:[/bold blue]")
    for ref in answer.references:
        console.print(f"- {ref}")

    # Print follow-up questions
    console.print("\n[bold blue]Follow-up Questions:[/bold blue]")
    for question in answer.followup_questions:
        console.print(f"- {question}")

except Exception as e:
    console.print(f"[bold red]Error:[/bold red] {str(e)}")
