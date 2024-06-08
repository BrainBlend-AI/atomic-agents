import os
from pydantic import BaseModel, Field
from typing import Optional
from rich.console import Console
import openai
import instructor
import requests

from atomic_agents.lib.tools.base import BaseTool, BaseToolConfig
from atomic_agents.lib.utils.scraping.url_to_markdown import UrlToMarkdownConverter
from atomic_agents.lib.utils.scraping.pdf_to_markdown import PdfToMarkdownConverter

################
# INPUT SCHEMA #
################
class ContentScrapingToolSchema(BaseModel):
    url: str = Field(..., description="URL of the web page or PDF to scrape.")

    class Config:
        title = "ContentScrapingTool"
        description = "Tool for scraping web pages or PDFs and converting content to markdown in order to extract information or summarize the content."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class ContentScrapingResultSchema(BaseModel):
    content: str
    metadata: Optional[dict] = None

class ContentScrapingToolOutputSchema(BaseModel):
    result: ContentScrapingResultSchema

##############
# TOOL LOGIC #
##############
class ContentScrapingToolConfig(BaseToolConfig):
    pass

class ContentScrapingTool(BaseTool):
    """
    Tool for scraping web pages or PDFs and converting content to markdown.

    Attributes:
        input_schema (ContentScrapingToolSchema): The schema for the input data.
        output_schema (ContentScrapingToolOutputSchema): The schema for the output data.
    """
    input_schema = ContentScrapingToolSchema
    output_schema = ContentScrapingToolOutputSchema

    def __init__(self, config: ContentScrapingToolConfig = ContentScrapingToolConfig()):
        """
        Initializes the ContentScrapingTool.

        Args:
            config (ContentScrapingToolConfig): Configuration for the tool.
        """
        super().__init__(config)

    def run(self, params: ContentScrapingToolSchema) -> ContentScrapingToolOutputSchema:
        """
        Runs the ContentScrapingTool with the given parameters.

        Args:
            params (ContentScrapingToolSchema): The input parameters for the tool, adhering to the input schema.

        Returns:
            ContentScrapingToolOutputSchema: The output of the tool, adhering to the output schema.
        """
        url = params.url
        response = requests.head(url)
        content_type = response.headers.get('Content-Type', '')

        if 'application/pdf' in content_type:
            document = PdfToMarkdownConverter.convert(url=url)
        else:
            document = UrlToMarkdownConverter.convert(url=url)

        result = ContentScrapingResultSchema(content=document.content, metadata=document.metadata.model_dump())
        return ContentScrapingToolOutputSchema(result=result)

#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()

    client = instructor.from_openai(
        openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    )

    #################
    # TEST WEB PAGE #
    #################
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=ContentScrapingTool.input_schema,
        messages=[{"role": "user", "content": "Scrape the content of https://example.com"}],
    )

    output = ContentScrapingTool().run(result)
    rich_console.print(f"Content: {output.result.content}, Metadata: {output.result.metadata}")
    
    ################
    # TEST PDF URL #
    ################
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=ContentScrapingTool.input_schema,
        messages=[{"role": "user", "content": "Scrape the content of https://pdfobject.com/pdf/sample.pdf"}],
    )
    
    output = ContentScrapingTool().run(result)
    rich_console.print(f"Content: {output.result.content}, Metadata: {output.result.metadata}")