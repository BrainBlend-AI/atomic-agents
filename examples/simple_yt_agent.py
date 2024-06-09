import os
import instructor
import openai
from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from typing import List, Optional

from atomic_agents.agents.base_chat_agent import BaseChatAgent
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator, SystemPromptInfo
from atomic_agents.lib.tools.yt_transcript_scraper import YouTubeTranscriptTool, YouTubeTranscriptToolConfig, YouTubeTranscriptToolSchema

console = Console()

# Initialize the client
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
client = instructor.from_openai(openai.OpenAI())

yt_scraper_tool = YouTubeTranscriptTool(config=YouTubeTranscriptToolConfig())

class YtTranscriptProvider(SystemPromptContextProviderBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transcript = None
        self.duration = None
        self.metadata = None
    
    def get_info(self) -> str:
        return f'VIDEO TRANSCRIPT: "{self.transcript}"\n\nDURATION: {self.duration}\n\nMETADATA: {self.metadata}'
        
transcript_provider = YtTranscriptProvider(title='YouTube Transcript')

# Define the system prompt information
system_prompt_info = SystemPromptInfo(
    background=[
        'This Assistant is an expert at extracting knowledge and other insightful and interesting information from YouTube transcripts.'
    ],
    steps=[
        'Analyse the YouTube transcript thoroughly to extract the most valuable insights, facts, and recommendations.',
        'Adhere strictly to the provided schema when extracting information from the input content.',
        'Ensure that the output matches the field descriptions, types and constraints exactly.',
    ],
    output_instructions=[
        'Only output Markdown-compatible strings.',
        'Ensure you follow ALL these instructions when creating your output.'
    ],
    context_providers={'yt_transcript': transcript_provider}
)

# Define the response model with detailed descriptions, constraints, and field types
class ResponseModel(BaseModel):
    summary: str = Field(..., description="A short summary of the content, including who is presenting and the content being discussed.")
    insights: List[str] = Field(..., min_items=5, max_items=5, description="exactly 5 of the best insights and ideas from the input.")
    quotes: List[str] = Field(None, min_items=5, max_items=5, description="exactly 5 of the most surprising, insightful, and/or interesting quotes from the input.")
    habits: Optional[List[str]] = Field(None, min_items=5, max_items=5, description="exactly 5 of the most practical and useful personal habits mentioned by the speakers.")
    facts: List[str] = Field(..., min_items=5, max_items=5, description="exactly 5 of the most surprising, insightful, and/or interesting valid facts about the greater world mentioned in the content.")
    recommendations: List[str] = Field(..., min_items=5, max_items=5, description="exactly 5 of the most surprising, insightful, and/or interesting recommendations from the content.")    
    references: List[str] = Field(..., description="All mentions of writing, art, tools, projects, and other sources of inspiration mentioned by the speakers.")
    one_sentence_takeaway: str = Field(..., description="The most potent takeaways and recommendations condensed into a single 20-word sentence.")

# Initialize the ToolInterfaceAgent with the SearxNGSearchTool
agent = BaseChatAgent(
    client=client,
    model='gpt-3.5-turbo',
    system_prompt_generator=SystemPromptGenerator(system_prompt_info),
    output_schema=ResponseModel
)

console.print("ToolInterfaceAgent with SearxNGSearchTool is ready.")

video_url = input('Enter the YouTube video URL: ')
scraped_transcript = yt_scraper_tool.run(YouTubeTranscriptToolSchema(video_url=video_url))
transcript_provider.transcript = scraped_transcript.transcript
transcript_provider.duration = scraped_transcript.duration
transcript_provider.metadata = scraped_transcript.metadata

response = agent.run('Perform your assignment on the YouTube video transcript present in your context. Do not reply with anything other than the output of the assignment.')

# Convert the ResponseModel to a dictionary and then to a Markdown string
response_dict = response.dict()

def format_markdown_section(title, items):
    if isinstance(items, list):
        return f"## {title}\n" + "\n".join([f"- {item}" for item in items]) + "\n"
    return f"## {title}\n{items}\n"

markdown_string = ""
for key, value in response_dict.items():
    title = key.replace('_', ' ').title()
    markdown_string += format_markdown_section(title, value)

# Print the response in a pretty Markdown formatted way
markdown_response = Markdown(markdown_string)
console.print(markdown_response)