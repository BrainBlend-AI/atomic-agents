import os
from examples.deep_research_multi_agent.agents.query_agent import query_agent
from examples.deep_research_multi_agent.agents.question_answering_agent import answer_agent
from examples.deep_research_multi_agent.agents.top_urls_selector_agent import top_urls_selector_agent
from examples.deep_research_multi_agent.agents.info_refiner_agent import refine_answer_agent
from examples.deep_research_multi_agent.providers import search_results_provider, vector_db_chunks_provider
from examples.deep_research_multi_agent.in_memory_faiss import InMemFaiss
from atomic_agents.lib.tools.search.searx_tool import SearxNGSearchTool, SearxNGSearchToolConfig
from rich.console import Console
import asyncio

async def main():
    
    console = Console()

    # Initialize the search tool
    search_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=30))
    in_mem_faiss = InMemFaiss(openai_api_key=os.getenv('OPENAI_API_KEY'))

    user_input = input("Enter your question (or type 'exit' to quit): ")

    answer_agent.register_context_provider('search_results', search_results_provider)
    top_urls_selector_agent.register_context_provider('search_results', search_results_provider)
    refine_answer_agent.register_context_provider('vector_db_chunks', vector_db_chunks_provider)

    while True:
        if user_input.lower() == 'exit':
            break

        console.print("[bold green]Getting queries...[/bold green]")
        queries = query_agent.run(query_agent.input_schema(instruction=user_input, num_queries=5))

        # Start loop here
        console.print("[bold green]Registering context providers...[/bold green]")

        console.print("[bold green]Getting search results...[/bold green]")
        search_results_provider.search_results = search_tool.run(search_tool.input_schema(**queries.model_dump()))
        
        # Select top URLs
        console.print("[bold green]Selecting top URLs...[/bold green]")
        top_urls = top_urls_selector_agent.run(top_urls_selector_agent.input_schema(
            user_input=user_input,
            num_urls=5
        ))

        # Call the answer agent
        console.print("[bold green]Calling the answer agent...[/bold green]")
        initial_answer = answer_agent.run(answer_agent.input_schema(question=user_input))
        console.print(initial_answer.markdown_output, markup=True)

        console.print("[bold green]=====================[/bold green]")

        console.print("[bold green]Ingesting URLs into in-memory FAISS...[/bold green]")
        await in_mem_faiss.ingest_urls(top_urls.top_urls)

        # Retrieve chunks
        console.print("[bold green]Retrieving chunks...[/bold green]")
        query = user_input
        top_k = 5
        chunks = in_mem_faiss.retrieve_chunks(query, top_k)

        vector_db_chunks_provider.chunks = chunks

        console.print("[bold green]Refining the answer...[/bold green]")
        refined_answer = refine_answer_agent.run(refine_answer_agent.input_schema(
            question=user_input,
            answer=initial_answer.markdown_output
        ))

        console.print("Refined Answer:")
        console.print(refined_answer.refined_answer, markup=True)

        # We don't need to keep the context for this agent after each run. This will save money.
        refine_answer_agent.reset_memory()

        user_input = input("Enter your question (or type 'exit' to quit): ")

# Run the main function
asyncio.run(main())