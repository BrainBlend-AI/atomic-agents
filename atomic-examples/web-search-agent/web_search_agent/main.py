import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from pydantic import Field

from atomic_agents import BaseIOSchema
from atomic_agents.context import ChatHistory, BaseDynamicContextProvider

from web_search_agent.tools.searxng_search import (
    SearXNGSearchTool,
    SearXNGSearchToolConfig,
    SearXNGSearchToolInputSchema,
    SearXNGSearchToolOutputSchema,
)

from web_search_agent.agents.query_agent import QueryAgentInputSchema, query_agent
from web_search_agent.agents.question_answering_agent import question_answering_agent, QuestionAnsweringAgentInputSchema


load_dotenv()

# Initialize a Rich Console for pretty console outputs
console = Console()

# History setup
history = ChatHistory()

# Initialize the SearXNGSearchTool
search_tool = SearXNGSearchTool(config=SearXNGSearchToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=5))


class SearchResultsProvider(BaseDynamicContextProvider):
    def __init__(self, title: str, search_results: SearXNGSearchToolOutputSchema | Exception):
        super().__init__(title=title)
        self.search_results = search_results

    def get_info(self) -> str:
        return f"{self.title}: {self.search_results}"


# Define input/output schemas for the main agent
class MainAgentInputSchema(BaseIOSchema):
    """Input schema for the main agent."""

    chat_message: str = Field(..., description="Chat message from the user.")


class MainAgentOutputSchema(BaseIOSchema):
    """Output schema for the main agent."""

    chat_message: str = Field(..., description="Response to the user's message.")


# Example usage
instruction = "Tell me about the Atomic Agents AI agent framework."
num_queries = 3
console.print(f"[bold blue]Instruction:[/bold blue] {instruction}")

while True:
    # Generate queries using the query agent
    query_input = QueryAgentInputSchema(instruction=instruction, num_queries=num_queries)
    generated_queries = query_agent.run(query_input)

    console.print("[bold blue]Generated Queries:[/bold blue]")
    for query in generated_queries.queries:
        console.print(f"- {query}")

    # Perform searches using the generated queries
    search_input = SearXNGSearchToolInputSchema(queries=generated_queries.queries, category="general")

    try:
        search_results = search_tool.run(search_input)
        search_results_provider = SearchResultsProvider("Search Results", search_results)
    except Exception as e:
        search_results_provider = SearchResultsProvider("Search Failed", e)

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
    for i, question in enumerate(answer.followup_questions, 1):
        console.print(f"[cyan]{i}. {question}[/cyan]")

    console.print()  # Add an empty line for better readability
    instruction = console.input("[bold blue]You:[/bold blue] ")
    if instruction.lower() in ["/exit", "/quit"]:
        console.print("Exiting chat...")
        break

    try:
        followup_question_id = int(instruction.strip())
        if 1 <= followup_question_id <= len(answer.followup_questions):
            instruction = answer.followup_questions[followup_question_id - 1]
            console.print(f"[bold blue]Follow-up Question:[/bold blue] {instruction}")
    except ValueError:
        pass
