import os
import asyncio
from typing import List
import rich
from atomic_agents.lib.tools.search.searxng_tool import SearxNGTool, SearxNGToolConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase
from examples.wiki_creator_agent.agents.query_agent import query_agent, QueryAgentInputSchema
from examples.wiki_creator_agent.agents.outline_agent import outline_agent, OutlineAgentInputSchema
from examples.wiki_creator_agent.agents.question_answering_agent import (
    question_answering_agent,
    QuestionAnsweringAgentInputSchema,
)
from examples.wiki_creator_agent.utils.scraper import ContentScraper
from examples.wiki_creator_agent.utils.vector_db import InMemFaiss
from examples.wiki_creator_agent.agents.article_writer_agent import (
    article_writer_agent,
    ArticleWriterAgentInputSchema,
    QuestionAnswer,
)

rich_console = rich.console.Console()


###################
# CONTEXT PROVIDERS #
###################
class SearchResultsProvider(SystemPromptContextProviderBase):
    def __init__(self, title="Search Results"):
        super().__init__(title)
        self.search_results = None

    def get_info(self) -> str:
        if self.search_results is None:
            return "No search results available."

        results_str = "Search Results:\n"
        for i, result in enumerate(self.search_results.results, 1):
            results_str += f"{i}. Title: {result.title}\n   URL: {result.url}\n   Content: {result.content[:100]}...\n\n"
        return results_str


class VectorDBResultsProvider(SystemPromptContextProviderBase):
    def __init__(self, title="Vector Database Results"):
        super().__init__(title)
        self.vector_db_results = None

    def get_info(self) -> str:
        if self.vector_db_results is None:
            return "No vector database results available."

        results_str = "Vector Database Results:\n\n"
        for i, chunk in enumerate(self.vector_db_results, 1):
            results_str += f"## RESULT {i}\n"
            results_str += f"{chunk}\n"
            results_str += "=" * 50 + "\n\n"

        return results_str


class OutlineProvider(SystemPromptContextProviderBase):
    def __init__(self, title="Article Outline"):
        super().__init__(title)
        self.outline = None

    def get_info(self) -> str:
        if self.outline is None:
            return "No outline available."

        outline_str = "Article Outline:\n"
        for section in self.outline:
            outline_str += f"Section: {section.title}\n"
            for subsection in section.subsections:
                outline_str += f"  Subsection: {subsection.title}\n"
        return outline_str


#############
# PIPELINES #
#############
class QueryAndSearchPipeline:
    @staticmethod
    def generate_queries_and_search(user_input: str, num_queries: int = 3):
        # Generate queries
        query_instruction = f"Generate research queries for an article about {user_input}"
        query_input = QueryAgentInputSchema(instruction=query_instruction, num_queries=num_queries)
        query_output = query_agent.run(query_input)
        queries = query_output.queries

        # Perform search
        search_tool_instance = SearxNGTool(config=SearxNGToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=30))
        search_input = SearxNGTool.input_schema(queries=queries)
        search_output = search_tool_instance.run(search_input)

        return queries, search_output


class OutlineGenerationPipeline:
    @staticmethod
    def generate_outline(user_input: str, search_results_provider):
        outline_agent.register_context_provider("search_results", search_results_provider)
        outline_input = OutlineAgentInputSchema(topic=user_input)
        outline_output = outline_agent.run(outline_input)
        return outline_output.outline

    @staticmethod
    def extract_urls_from_outline(outline):
        urls = set()
        for section in outline:
            urls.update(url for point in section.questions_to_answer for url in point.potential_sources)
            for subsection in section.subsections:
                urls.update(url for point in subsection.questions_to_answer for url in point.potential_sources)
        return sorted(list(urls))


class ContentScrapingPipeline:
    @staticmethod
    async def scrape_and_ingest_urls(urls: List[str], batch_size: int = 5):
        faiss_db = InMemFaiss(openai_api_key=os.getenv("OPENAI_API_KEY"))
        batches = [urls[i : i + batch_size] for i in range(0, len(urls), batch_size)]

        for batch_num, batch in enumerate(batches, 1):
            rich_console.print(f"[bold magenta]Scraping and ingesting batch {batch_num} of {len(batches)}[/bold magenta]")
            scraped_content = await ContentScraper.scrape_urls(batch)
            await faiss_db.ingest_documents(scraped_content)

            for url in scraped_content.keys():
                rich_console.print(f"[green]Ingested content from {url}[/green]")

        return faiss_db


class QuestionAnsweringPipeline:
    @staticmethod
    async def answer_questions(outline, faiss_db, faiss_db_context_provider, outline_provider):
        question_answering_agent.register_context_provider("vector_db_results", faiss_db_context_provider)
        question_answering_agent.register_context_provider("outline", outline_provider)

        qa_pairs = []

        for section in outline:
            for subsection in section.subsections:
                questions_to_answer = "\n".join([item.question for item in subsection.questions_to_answer])
                context = faiss_db.retrieve_chunks(questions_to_answer)
                faiss_db_context_provider.vector_db_results = context

                for question_item in subsection.questions_to_answer:
                    question_input = QuestionAnsweringAgentInputSchema(question=question_item.question)
                    answer_output = question_answering_agent.run(question_input)

                    rich_console.print(f"[bold cyan]Question:[/bold cyan] {question_item.question}")
                    rich_console.print(f"[bold green]Answer:[/bold green] {answer_output.answer}\n")

                    qa_pairs.append(QuestionAnswer(question=question_item.question, answer=answer_output.answer))

        return qa_pairs


class ArticleWritingPipeline:
    @staticmethod
    def write_article(topic: str, outline, qa_pairs):
        input_data = ArticleWriterAgentInputSchema(topic=topic, outline=outline, qa_pairs=qa_pairs)
        output = article_writer_agent.run(input_data)
        return output.article


###################
# MAIN APPLICATION #
###################
class WikiCreatorApplication:
    def __init__(self):
        self.rich_console = rich.console.Console()
        self.search_results_provider = SearchResultsProvider()
        self.vector_db_results_provider = VectorDBResultsProvider()
        self.outline_provider = OutlineProvider()
        self.qa_pairs = []

    async def run(self):
        self.rich_console.print("[bold blue]Script execution started[/bold blue]")
        user_input = input("I want to write an article about ")

        queries, search_output = QueryAndSearchPipeline.generate_queries_and_search(user_input, num_queries=5)
        self.rich_console.print("[bold yellow]Generated Queries:[/bold yellow]")
        for i, query in enumerate(queries, 1):
            self.rich_console.print(f"[yellow]{i}. {query}[/yellow]")
        self.rich_console.print()

        self.search_results_provider.search_results = search_output

        outline = OutlineGenerationPipeline.generate_outline(user_input, self.search_results_provider)
        self.rich_console.print("[bold green]Generated Outline:[/bold green]")
        self.rich_console.print(outline)

        urls = OutlineGenerationPipeline.extract_urls_from_outline(outline)
        self.rich_console.print("\n[bold cyan]Extracted Potential Source URLs:[/bold cyan]")
        for i, url in enumerate(urls, 1):
            self.rich_console.print(f"[cyan]{i}. {url}[/cyan]")

        batch_size = 10  # You can change this value or make it configurable
        faiss_db = await ContentScrapingPipeline.scrape_and_ingest_urls(urls, batch_size)

        self.outline_provider.outline = outline
        self.qa_pairs = await QuestionAnsweringPipeline.answer_questions(
            outline, faiss_db, self.vector_db_results_provider, self.outline_provider
        )

        # New code for article writing
        self.rich_console.print("[bold magenta]Writing the article...[/bold magenta]")
        article = ArticleWritingPipeline.write_article(user_input, outline, self.qa_pairs)

        self.rich_console.print("[bold green]Article generated successfully![/bold green]")
        self.rich_console.print("\n[bold cyan]Generated Article:[/bold cyan]")
        self.rich_console.print(article)

        # Optionally, save the article to a file
        with open("generated_article.md", "w", encoding="utf-8") as f:
            f.write(article)
        self.rich_console.print("\n[bold green]Article saved to 'generated_article.md'[/bold green]")


####################
# SCRIPT EXECUTION #
####################
async def main():
    app = WikiCreatorApplication()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
