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

from rich import print


def perform_search_and_update_context(
    user_message: str, scraped_content_context_provider: ScrapedContentContextProvider
) -> None:
    # Generate search queries
    query_agent_output = query_agent.run(QueryAgentInputSchema(instruction=user_message, num_queries=3))
    queries = query_agent_output.queries
    print("Generated queries:", queries)

    # Perform the search
    searxng_search_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url="http://localhost:8080/"))
    search_results = searxng_search_tool.run(SearxNGSearchToolInputSchema(queries=queries))

    # Scrape content from search results
    webpage_scraper_tool = WebpageScraperTool()
    results_for_context_provider = []

    for result in search_results.results[:3]:
        scraped_content = webpage_scraper_tool.run(WebpageScraperToolInputSchema(url=result.url, include_links=True))
        results_for_context_provider.append(ContentItem(content=scraped_content.content, url=result.url))

    # Update the context provider with new content
    scraped_content_context_provider.content_items = results_for_context_provider


def get_answer(user_message: str) -> tuple[str, list[str]]:
    question_answering_agent_output = question_answering_agent.run(QuestionAnsweringAgentInputSchema(question=user_message))
    return question_answering_agent_output.answer, question_answering_agent_output.follow_up_questions


def initialize_conversation_memory() -> None:
    """Initialize the agent's memory with an example conversation showing good follow-up questions."""

    # Create the initial user message using the input schema
    initial_question = QuestionAnsweringAgentInputSchema(question="Tell me about quantum computing.")

    # Create the initial response using the output schema
    initial_answer = QuestionAnsweringAgentOutputSchema(
        answer=(
            "Quantum computing is a revolutionary technology that uses quantum mechanics to perform computations."
            "Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or 'qubits' "
            "that can exist in multiple states simultaneously due to superposition."
        ),
        follow_up_questions=[
            "What are the main challenges in building a practical quantum computer?",
            "How does quantum entanglement contribute to quantum computing power?",
            "Which companies are currently leading quantum computing research?",
            "What types of problems are quantum computers especially good at solving?",
        ],
    )

    # Add messages to the agent's memory using proper schema instances
    question_answering_agent.memory.add_message("user", initial_question)
    question_answering_agent.memory.add_message("assistant", initial_answer)


def chat_loop() -> None:
    # Initialize context providers
    scraped_content_context_provider = ScrapedContentContextProvider("Scraped Content")
    current_date_context_provider = CurrentDateContextProvider("Current Date")

    # Register context providers
    choice_agent.register_context_provider("current_date", current_date_context_provider)
    question_answering_agent.register_context_provider("current_date", current_date_context_provider)
    query_agent.register_context_provider("current_date", current_date_context_provider)

    choice_agent.register_context_provider("scraped_content", scraped_content_context_provider)
    question_answering_agent.register_context_provider("Scraped Content", scraped_content_context_provider)

    # Initialize conversation memory with example
    initialize_conversation_memory()

    print("\n=== Welcome to the Deep Research Chat! ===")
    print("Type 'exit' to end the conversation.\n")
    print("I can help you research and learn about any topic. I'll provide detailed answers")
    print("and suggest specific follow-up questions to deepen your understanding.\n")

    print("Here are some example questions to get started:")
    starter_questions = [
        "What are the latest breakthroughs in quantum computing?",
        "How does artificial intelligence impact climate change research?",
        "What are the most promising renewable energy technologies?",
        "What discoveries led to the latest Nobel Prize in Physics?",
        "How do black holes affect the structure of galaxies?",
    ]

    print("\n[bold blue]Suggested Topics:[/bold blue]")
    for i, question in enumerate(starter_questions, 1):
        print(f"  {i}. {question}")
    print("\n-------------------------------------------")

    while True:
        user_message = input("\nYour question: ").strip()

        if user_message.lower() == "exit":
            print("Goodbye!")
            break

        # Determine if we need a new search
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

        if choice_agent_output.decision:
            print("\n[bold yellow]Performing new search[/bold yellow]")
            print(f"Reason: {choice_agent_output.reasoning}")

            # Perform search and update context
            perform_search_and_update_context(user_message, scraped_content_context_provider)
        else:
            print("\n[bold green]Using existing context[/bold green]")
            print(f"Reason: {choice_agent_output.reasoning}")

        # Get and display the answer
        answer, follow_up_questions = get_answer(user_message)

        print("\nAnswer:", answer)
        if follow_up_questions:
            print("\nSome questions you could ask to learn more about this topic:")
            for i, question in enumerate(follow_up_questions, 1):
                print(f"{i}. {question}")


if __name__ == "__main__":
    chat_loop()
