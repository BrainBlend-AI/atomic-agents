import os
from pydantic import BaseModel, Field
from typing import List, Optional
from rich.console import Console
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from atomic_agents.agents.base_chat_agent import BaseAgentIO
from atomic_agents.lib.tools.base import BaseTool, BaseToolConfig
from googleapiclient.discovery import build

################
# INPUT SCHEMA #
################
class YouTubeTranscriptToolSchema(BaseAgentIO):
    video_url: str = Field(..., description="URL of the YouTube video to fetch the transcript for.")
    language: Optional[str] = Field(None, description="Language code for the transcript (e.g., 'en' for English).")

    class Config:
        title = "YouTubeTranscriptTool"
        description = "Tool for fetching the transcript of a YouTube video using the YouTube Transcript API. Returns the transcript with text, start time, and duration."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class YouTubeTranscriptToolOutputSchema(BaseAgentIO):
    transcript: str
    duration: float
    comments: List[str]
    metadata: dict
    
    class Config:
        title = "YouTubeTranscriptToolOutput"
        description = "Output schema for the YouTubeTranscriptTool. Contains the transcript text, duration, comments, and metadata."
        json_schema_extra = {
            "title": title,
            "description": description
        }
        

##############
# TOOL LOGIC #
##############
class YouTubeTranscriptToolConfig(BaseToolConfig):
    api_key: str = Field(description="YouTube API key for fetching video metadata.", default=os.getenv('YOUTUBE_API_KEY'))

class YouTubeTranscriptTool(BaseTool):
    """
    Tool for fetching the transcript of a YouTube video using the YouTube Transcript API.

    Attributes:
        input_schema (YouTubeTranscriptToolSchema): The schema for the input data.
        output_schema (YouTubeTranscriptToolOutputSchema): The schema for the output data.
    """
    input_schema = YouTubeTranscriptToolSchema
    output_schema = YouTubeTranscriptToolOutputSchema

    def __init__(self, config: YouTubeTranscriptToolConfig):
        """
        Initializes the YouTubeTranscriptTool.

        Args:
            config (YouTubeTranscriptToolConfig): Configuration for the tool.
        """
        super().__init__(config)
        self.api_key = config.api_key

    def run(self, params: YouTubeTranscriptToolSchema) -> YouTubeTranscriptToolOutputSchema:
        """
        Runs the YouTubeTranscriptTool with the given parameters.

        Args:
            params (YouTubeTranscriptToolSchema): The input parameters for the tool, adhering to the input schema.

        Returns:
            YouTubeTranscriptToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            Exception: If fetching the transcript fails.
        """
        video_id = self.extract_video_id(params.video_url)
        try:
            if params.language:
                transcripts = YouTubeTranscriptApi.get_transcript(video_id, languages=[params.language])
            else:
                transcripts = YouTubeTranscriptApi.get_transcript(video_id)
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            raise Exception(f"Failed to fetch transcript for video '{video_id}': {str(e)}")

        transcript_text = " ".join([transcript['text'] for transcript in transcripts])
        total_duration = sum([transcript['duration'] for transcript in transcripts])

        metadata = self.fetch_video_metadata(video_id)

        return YouTubeTranscriptToolOutputSchema(
            transcript=transcript_text,
            duration=total_duration,
            comments=[],
            metadata=metadata
        )

    @staticmethod
    def extract_video_id(url: str) -> str:
        """
        Extracts the video ID from a YouTube URL.

        Args:
            url (str): The YouTube video URL.

        Returns:
            str: The extracted video ID.
        """
        return url.split('v=')[-1].split('&')[0]

    def fetch_video_metadata(self, video_id: str) -> dict:
        """
        Fetches metadata for a YouTube video.

        Args:
            video_id (str): The YouTube video ID.

        Returns:
            dict: The metadata of the video.
        """
        youtube = build('youtube', 'v3', developerKey=self.api_key)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        if not response['items']:
            raise Exception(f"No metadata found for video '{video_id}'")

        video_info = response['items'][0]['snippet']
        metadata = {
            "id": video_id,
            "title": video_info['title'],
            "channel": video_info['channelTitle'],
            "published_at": video_info['publishedAt']
        }
        return metadata

#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    api_key = os.getenv('YOUTUBE_API_KEY')
    search_tool_instance = YouTubeTranscriptTool(config=YouTubeTranscriptToolConfig(api_key=api_key))
    
    search_input = YouTubeTranscriptTool.input_schema(video_url="https://www.youtube.com/watch?v=t1e8gqXLbsU", language="en")

    output = search_tool_instance.run(search_input)
    rich_console.print(output)