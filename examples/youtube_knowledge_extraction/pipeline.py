from typing import Dict, List, Type
from pydantic import Field
from rich.console import Console
from rich.markdown import Markdown

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.tools.yt_transcript_scraper_tool import (
    YouTubeTranscriptTool,
    YouTubeTranscriptToolConfig,
    YouTubeTranscriptToolInputSchema,
)

from agents.youtube_knowledge_extraction_agent import (
    youtube_knowledge_extraction_agent,
    YouTubeKnowledgeExtractionInputSchema,
    YouTubeKnowledgeExtractionOutputSchema,
    transcript_provider,
)

console = Console()

# Type aliases
SchemaType = Type[BaseIOSchema]
OrchestrationGraphType = Dict[BaseIOSchema, List[BaseIOSchema]]

# Tool initialization
yt_scraper_tool = YouTubeTranscriptTool(config=YouTubeTranscriptToolConfig())


# Schema models
class InputSchema(BaseIOSchema):
    """This schema defines the input for the pipeline."""

    user_input: str = Field(..., description="The YouTube video URL provided by the user.")


class ChatReplySchema(BaseIOSchema):
    """This schema defines a standard chat reply."""

    chat_message: str = Field(..., description="The chat message to be sent back to the user.")


# Orchestration flow config
OrchestrationGraph: OrchestrationGraphType = {
    InputSchema: [YouTubeKnowledgeExtractionInputSchema],
    YouTubeKnowledgeExtractionInputSchema: [YouTubeKnowledgeExtractionOutputSchema],
    YouTubeKnowledgeExtractionOutputSchema: [ChatReplySchema],
}


def format_markdown_section(title, items):
    if isinstance(items, list):
        return f"## {title}\n" + "\n".join([f"- {item}" for item in items]) + "\n"
    return f"## {title}\n{items}\n"


def run_pipeline(video_url: str):
    # Step 1: Scrape YouTube transcript
    scraped_transcript = yt_scraper_tool.run(YouTubeTranscriptToolInputSchema(video_url=video_url))
    transcript_provider.transcript = scraped_transcript.transcript
    transcript_provider.duration = scraped_transcript.duration
    transcript_provider.metadata = scraped_transcript.metadata

    # Step 2: Run YouTube knowledge extraction agent
    response = youtube_knowledge_extraction_agent.run(YouTubeKnowledgeExtractionInputSchema(video_url=video_url))

    # Step 3: Format and display the response
    response_dict = response.model_dump()
    markdown_string = ""
    for key, value in response_dict.items():
        title = key.replace("_", " ").title()
        markdown_string += format_markdown_section(title, value)

    markdown_response = Markdown(markdown_string)
    console.print(markdown_response)


if __name__ == "__main__":
    video_url = input("Enter the YouTube video URL: ")
    run_pipeline(video_url)
