from deep_research.agents.query_agent import QueryAgentInputSchema, query_agent
from deep_research.agents.qa_agent import (
    QuestionAnsweringAgentInputSchema,
    question_answering_agent,
    QuestionAnsweringAgentOutputSchema,
)
from deep_research.agents.choice_agent import choice_agent, ChoiceAgentInputSchema
from deep_research.tools.searxng_search import SearxNGSearchTool, SearxNGSearchToolConfig, SearxNGSearchToolInputSchema
from deep_research.tools.webpage_scraper import WebpageScraperTool, WebpageScraperToolInputSchema
from deep_research.context_providers import ContentItem, CurrentDateContextProvider, ScrapedContentContextProvider

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()

WELCOME_MESSAGE = (
    "Welcome to Deep Research - your AI-powered research assistant! I can help you explore and "
    "understand any topic through detailed research and interactive discussion."
)

STARTER_QUESTIONS = [
    "Can you help me research the latest AI news?",
    "Who won the Nobel Prize in Physics this year?",
    "Where can I learn more about quantum computing?",
]


def perform_search_and_update_context(
    user_message: str, scraped_content_context_provider: ScrapedContentContextProvider
) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Generate search queries
        task = progress.add_task("[cyan]Generating search queries...", total=None)
        console.print("\n[bold yellow]🤔 Analyzing your question to generate relevant search queries...[/bold yellow]")
        query_agent_output = query_agent.run(QueryAgentInputSchema(instruction=user_message, num_queries=3))
        progress.remove_task(task)

        console.print("\n[bold green]🔍 Generated search queries:[/bold green]")
        for i, query in enumerate(query_agent_output.queries, 1):
            console.print(f"  {i}. [italic]{query}[/italic]")

        # Perform the search
        task = progress.add_task("[cyan]Searching the web...", total=None)
        console.print("\n[bold yellow]🌐 Searching across the web using SearxNG...[/bold yellow]")
        searxng_search_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url="http://localhost:8080/"))
        search_results = searxng_search_tool.run(SearxNGSearchToolInputSchema(queries=query_agent_output.queries))
        progress.remove_task(task)

        # Scrape content from search results
        console.print("\n[bold green]📑 Found relevant web pages:[/bold green]")
        for i, result in enumerate(search_results.results[:3], 1):
            console.print(f"  {i}. [link={result.url}]{result.title}[/link]")

        task = progress.add_task("[cyan]Scraping webpage content...", total=None)
        console.print("\n[bold yellow]📥 Extracting content from web pages...[/bold yellow]")
        webpage_scraper_tool = WebpageScraperTool()
        results_for_context_provider = []

        for result in search_results.results[:3]:
            scraped_content = webpage_scraper_tool.run(WebpageScraperToolInputSchema(url=result.url, include_links=True))
            results_for_context_provider.append(ContentItem(content=scraped_content.content, url=result.url))
        progress.remove_task(task)

        # Update the context provider with new content
        console.print("\n[bold green]🔄 Updating research context with new information...[/bold green]")
        scraped_content_context_provider.content_items = results_for_context_provider


def initialize_conversation() -> None:
    initial_answer = QuestionAnsweringAgentOutputSchema(
        answer=WELCOME_MESSAGE,
        follow_up_questions=STARTER_QUESTIONS,
    )
    question_answering_agent.memory.add_message("assistant", initial_answer)


def display_welcome() -> None:
    welcome_panel = Panel(
        WELCOME_MESSAGE, title="[bold blue]Deep Research Chat[/bold blue]", border_style="blue", padding=(1, 2)
    )
    console.print("\n")
    console.print(welcome_panel)

    # Create a table for starter questions
    table = Table(
        show_header=True, header_style="bold cyan", box=box.ROUNDED, title="[bold]Example Questions to Get Started[/bold]"
    )
    table.add_column("№", style="dim", width=4)
    table.add_column("Question", style="green")

    for i, question in enumerate(STARTER_QUESTIONS, 1):
        table.add_row(str(i), question)

    console.print("\n")
    console.print(table)
    console.print("\n" + "─" * 80 + "\n")


def display_search_status(is_new_search: bool, reasoning: str) -> None:
    if is_new_search:
        panel = Panel(
            f"[white]{reasoning}[/white]",
            title="[bold yellow]Performing New Search[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    else:
        panel = Panel(
            f"[white]{reasoning}[/white]",
            title="[bold green]Using Existing Context[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    console.print("\n")
    console.print(panel)


def display_answer(answer: str, follow_up_questions: list[str]) -> None:
    # Display the main answer in a panel
    answer_panel = Panel(Markdown(answer), title="[bold blue]Answer[/bold blue]", border_style="blue", padding=(1, 2))
    console.print("\n")
    console.print(answer_panel)

    # Display follow-up questions if available
    if follow_up_questions:
        questions_table = Table(
            show_header=True, header_style="bold cyan", box=box.ROUNDED, title="[bold]Follow-up Questions[/bold]"
        )
        questions_table.add_column("№", style="dim", width=4)
        questions_table.add_column("Question", style="green")

        for i, question in enumerate(follow_up_questions, 1):
            questions_table.add_row(str(i), question)

        console.print("\n")
        console.print(questions_table)


def chat_loop() -> None:
    console.print("\n[bold magenta]🚀 Initializing Deep Research System...[/bold magenta]")

    # Initialize context providers
    console.print("[dim]• Creating context providers...[/dim]")
    scraped_content_context_provider = ScrapedContentContextProvider("Scraped Content")
    current_date_context_provider = CurrentDateContextProvider("Current Date")

    # Register context providers
    console.print("[dim]• Registering context providers with agents...[/dim]")
    choice_agent.register_context_provider("current_date", current_date_context_provider)
    question_answering_agent.register_context_provider("current_date", current_date_context_provider)
    query_agent.register_context_provider("current_date", current_date_context_provider)

    choice_agent.register_context_provider("scraped_content", scraped_content_context_provider)
    question_answering_agent.register_context_provider("scraped_content", scraped_content_context_provider)
    query_agent.register_context_provider("scraped_content", scraped_content_context_provider)

    console.print("[dim]• Initializing conversation memory...[/dim]")
    initialize_conversation()

    console.print("[bold green]✨ System initialized successfully![/bold green]\n")
    display_welcome()

    while True:
        user_message = console.input("\n[bold blue]Your question:[/bold blue] ").strip()

        if user_message.lower() == "exit":
            console.print("\n[bold]👋 Goodbye! Thanks for using Deep Research.[/bold]")
            break

        console.print("\n[bold yellow]🤖 Processing your question...[/bold yellow]")

        # Determine if we need a new search
        console.print("[dim]• Evaluating if new research is needed...[/dim]")
        choice_agent_output = choice_agent.run(
            ChoiceAgentInputSchema(
                user_message=user_message,
                decision_type=(
                    "Should we perform a new web search? TRUE if we need new or updated information, FALSE if existing "
                    "context is sufficient. Consider: 1) Is the context empty? 2) Is the existing information relevant? "
                    "3) Is the information recent enough?"
                ),
            )
        )

        # Display search status with new formatting
        display_search_status(choice_agent_output.decision, choice_agent_output.reasoning)

        if choice_agent_output.decision:
            perform_search_and_update_context(user_message, scraped_content_context_provider)

        # Get and display the answer with new formatting
        console.print("\n[bold yellow]🎯 Generating comprehensive answer...[/bold yellow]")
        question_answering_agent_output = question_answering_agent.run(
            QuestionAnsweringAgentInputSchema(question=user_message)
        )

        display_answer(question_answering_agent_output.answer, question_answering_agent_output.follow_up_questions)


if __name__ == "__main__":
    chat_loop()
