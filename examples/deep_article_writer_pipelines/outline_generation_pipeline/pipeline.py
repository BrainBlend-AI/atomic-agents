import os
from agents.query_gen_agent import query_gen_agent, QueryAgentInputSchema
from agents.outline_gen_agent import outline_gen_agent, OutlineAgentInputSchema
from atomic_agents.lib.tools.search.searxng_tool import SearxNGTool, SearxNGToolConfig

# Initialize the SearxNG tool
searxng_tool = SearxNGTool(config=SearxNGToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=5))


def run_pipeline(instruction: str):
    # Step 1: Generate queries using the query_gen_agent
    query_input = QueryAgentInputSchema(instruction=instruction, num_queries=3)
    generated_queries = query_gen_agent.run(query_input)

    print("Generated queries:")
    for i, query in enumerate(generated_queries.queries, 1):
        print(f"{i}. {query}")

    # Step 2: Use the generated queries with the SearxNG tool
    search_input = SearxNGTool.input_schema(queries=generated_queries.queries, category="general")
    search_results = searxng_tool.run(search_input)

    print("\nSearch results:")
    for i, result in enumerate(search_results.results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Content: {result.content[:100]}...")  # Print first 100 characters of content

    # Step 3: Generate article outline
    outline_input = OutlineAgentInputSchema(instruction=instruction, search_results=search_results.results)
    outline = outline_gen_agent.run(outline_input)

    print("\nArticle Outline:")
    print(f"Title: {outline.article_title}")
    print("Sections:")
    for i, section in enumerate(outline.section_titles, 1):
        print(f"{i}. {section}")

    print("\nReasoning and Analysis:")
    for i, step in enumerate(outline.reasoning_and_analysis, 1):
        print(f"{i}. {step}")


if __name__ == "__main__":
    instruction = "Explain the impact of artificial intelligence on modern healthcare"
    run_pipeline(instruction)
