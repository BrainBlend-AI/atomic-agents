import os
import instructor
import openai
from pydantic import BaseModel
from rich.console import Console
from rich.markdown import Markdown

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

system_prompt_info = SystemPromptInfo(
    background=[
        'Extract surprising, insightful, and interesting information from text content. Focus on insights related to the purpose and meaning of life, human flourishing, the role of technology in the future of humanity, artificial intelligence and its effect on humans, memes, learning, reading, books, continuous improvement, and similar topics.'
    ],
    steps=[
        'SUMMARY: Extract a 25-word summary of the content, including who is presenting and the content being discussed.',
        'IDEAS: Extract 20 to 50 of the most surprising, insightful, and/or interesting ideas from the input.',
        'INSIGHTS: Extract 10 to 20 of the best insights from the input and the IDEAS section.',
        'QUOTES: Extract 15 to 30 of the most surprising, insightful, and/or interesting quotes from the input.',
        'HABITS: Extract 15 to 30 of the most practical and useful personal habits mentioned by the speakers.',
        'FACTS: Extract 15 to 30 of the most surprising, insightful, and/or interesting valid facts about the greater world mentioned in the content.',
        'REFERENCES: Extract all mentions of writing, art, tools, projects, and other sources of inspiration mentioned by the speakers.',
        'ONE-SENTENCE TAKEAWAY: Extract the most potent takeaway and recommendation into a 15-word sentence.',
        'RECOMMENDATIONS: Extract 15 to 30 of the most surprising, insightful, and/or interesting recommendations from the content.'
    ],
    output_instructions=[
        'Only output Markdown.',
        'Write IDEAS, RECOMMENDATIONS, HABITS, FACTS, and INSIGHTS bullets as exactly 15 words.',
        'Extract at least 25 IDEAS, 10 INSIGHTS, and 20 items for other sections.',
        'Do not give warnings or notes; only output the requested sections.',
        'Use bulleted lists for output, not numbered lists.',
        'Do not repeat ideas, quotes, facts, or resources.',
        'Do not start items with the same opening words.',
        'Ensure you follow ALL these instructions when creating your output.',
        'Do not reply to the user\'s input with anything except the final output of the assignment.'
    ],
    context_providers={'yt_transcript': transcript_provider}
)

class ResponseModel(BaseModel):
    summary: str
    ideas: list[str]
    insights: list[str]
    quotes: list[str]
    habits: list[str]
    facts: list[str]
    references: list[str]
    one_sentence_takeaway: str

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
