import os
from pydantic import BaseModel, Field
from typing import Optional
from rich.console import Console
import openai
import instructor
import requests

from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.lib.scraping.url_to_markdown import UrlToMarkdownConverter
from atomic_agents.lib.scraping.pdf_to_markdown import PdfToMarkdownConverter
from atomic_agents.lib.models.web_document import WebDocument

################
# INPUT SCHEMA #
################
class WebScrapingToolSchema(BaseModel):
    url: str = Field(..., description="URL of the web page to scrape.")

    class Config:
        title = "WebScrapingTool"
        description = "Tool for scraping web pages and converting content to markdown in order to extract information or summarize the content."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class WebScrapingResultSchema(BaseModel):
    content: str
    metadata: Optional[dict] = None

class WebScrapingToolOutputSchema(BaseModel):
    result: WebScrapingResultSchema

##############
# TOOL LOGIC #
##############
class WebScrapingTool(BaseTool):
    input_schema = WebScrapingToolSchema
    output_schema = WebScrapingToolOutputSchema
    
    def __init__(self, tool_description_override: Optional[str] = None):
        super().__init__(tool_description_override)

    def run(self, params: WebScrapingToolSchema) -> WebScrapingToolOutputSchema:
        url = params.url
        response = requests.head(url)
        content_type = response.headers.get('Content-Type', '')

        if 'application/pdf' in content_type:
            document = PdfToMarkdownConverter.convert(url=url)
        else:
            document = UrlToMarkdownConverter.convert(url=url)

        result = WebScrapingResultSchema(content=document.content, metadata=document.metadata.model_dump())
        return WebScrapingToolOutputSchema(result=result)

#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()

    # Initialize the client outside
    client = instructor.from_openai(
        openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    )

    # Extract structured data from natural language
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=WebScrapingTool.input_schema,
        messages=[{"role": "user", "content": "Scrape the content of https://example.com"}],
    )

    # Print the result
    output = WebScrapingTool().run(result)
    rich_console.print(f"Content: {output.result.content}, Metadata: {output.result.metadata}")