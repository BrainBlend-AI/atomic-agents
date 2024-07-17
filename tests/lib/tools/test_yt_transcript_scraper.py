import pytest
from unittest.mock import patch, Mock
from pydantic import ValidationError
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from atomic_agents.lib.tools.yt_transcript_scraper import YouTubeTranscriptToolSchema
from atomic_agents.lib.tools.yt_transcript_scraper import (
    YouTubeTranscriptTool,
    YouTubeTranscriptToolConfig,
    YouTubeTranscriptToolSchema,
    YouTubeTranscriptToolOutputSchema,
)
from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.agents.base_agent import BaseIOSchema
from youtube_transcript_api import YouTubeTranscriptApi


# Sample data
SAMPLE_TRANSCRIPT = [
    {"text": "This is the first part of the transcript.", "start": 0.0, "duration": 5.0},
    {"text": "This is the second part.", "start": 5.0, "duration": 3.0},
]

SAMPLE_VIDEO_INFO = {
    "id": "dQw4w9WgXcQ",
    "title": "Sample Video",
    "channel": "Sample Channel",
    "published_at": "2023-01-01T00:00:00Z",
}

@pytest.fixture
def youtube_transcript_tool():
    config = YouTubeTranscriptToolConfig(api_key="dummy_api_key")
    return YouTubeTranscriptTool(config)

def test_youtube_transcript_tool_initialization(youtube_transcript_tool):
    assert isinstance(youtube_transcript_tool, BaseTool)
    assert youtube_transcript_tool.api_key == "dummy_api_key"

def test_youtube_transcript_tool_input_schema():
    assert issubclass(YouTubeTranscriptToolSchema, BaseIOSchema)
    assert "video_url" in YouTubeTranscriptToolSchema.model_fields
    assert "language" in YouTubeTranscriptToolSchema.model_fields

def test_youtube_transcript_tool_output_schema():
    assert issubclass(YouTubeTranscriptToolOutputSchema, BaseIOSchema)
    assert "transcript" in YouTubeTranscriptToolOutputSchema.model_fields
    assert "duration" in YouTubeTranscriptToolOutputSchema.model_fields
    assert "comments" in YouTubeTranscriptToolOutputSchema.model_fields
    assert "metadata" in YouTubeTranscriptToolOutputSchema.model_fields

def test_extract_video_id():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_id = YouTubeTranscriptTool.extract_video_id(url)
    assert video_id == "dQw4w9WgXcQ"

@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.extract_video_id')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.fetch_video_metadata')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptApi.get_transcript')
def test_run(mock_get_transcript, mock_fetch_metadata, mock_extract_video_id, youtube_transcript_tool):
    mock_extract_video_id.return_value = "dQw4w9WgXcQ"
    mock_fetch_metadata.return_value = SAMPLE_VIDEO_INFO
    mock_get_transcript.return_value = SAMPLE_TRANSCRIPT
    
    input_data = YouTubeTranscriptToolSchema(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    result = youtube_transcript_tool.run(input_data)
    
    assert isinstance(result, YouTubeTranscriptToolOutputSchema)
    assert result.transcript == "This is the first part of the transcript. This is the second part."
    assert result.duration == 8.0
    assert result.comments == []
    assert result.metadata == SAMPLE_VIDEO_INFO

@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.extract_video_id')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.fetch_video_metadata')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptApi.get_transcript')
def test_run_with_language(mock_get_transcript, mock_fetch_metadata, mock_extract_video_id, youtube_transcript_tool):
    mock_extract_video_id.return_value = "dQw4w9WgXcQ"
    mock_fetch_metadata.return_value = SAMPLE_VIDEO_INFO
    mock_get_transcript.return_value = SAMPLE_TRANSCRIPT
    
    input_data = YouTubeTranscriptToolSchema(
        video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        language="en"
    )
    youtube_transcript_tool.run(input_data)
    
    mock_get_transcript.assert_called_once_with("dQw4w9WgXcQ", languages=["en"])

@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.extract_video_id')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.fetch_video_metadata')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptApi.get_transcript')
def test_run_transcript_not_found(mock_get_transcript, mock_fetch_metadata, mock_extract_video_id, youtube_transcript_tool):
    mock_extract_video_id.return_value = "dQw4w9WgXcQ"
    mock_fetch_metadata.return_value = SAMPLE_VIDEO_INFO
    mock_get_transcript.side_effect = Exception("No transcript found")
    
    input_data = YouTubeTranscriptToolSchema(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    with pytest.raises(Exception, match="No transcript found"):
        youtube_transcript_tool.run(input_data)

def test_youtube_transcript_tool_config_validation():
    with pytest.raises(ValidationError):
        YouTubeTranscriptToolConfig(api_key=None)  # api_key is required and should not be None

    config = YouTubeTranscriptToolConfig(api_key="dummy_api_key")
    assert config.api_key == "dummy_api_key"
    
@patch.object(YouTubeTranscriptApi, 'get_transcript')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.fetch_video_metadata')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.extract_video_id')
def test_run_no_transcript_found(mock_extract_video_id, mock_fetch_metadata, mock_get_transcript, youtube_transcript_tool):
    mock_extract_video_id.return_value = "dQw4w9WgXcQ"
    mock_fetch_metadata.return_value = SAMPLE_VIDEO_INFO
    mock_get_transcript.side_effect = NoTranscriptFound("dQw4w9WgXcQ", "en", "Transcript not found")
    
    input_data = YouTubeTranscriptToolSchema(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    with pytest.raises(Exception, match="Failed to fetch transcript for video 'dQw4w9WgXcQ': "):
        youtube_transcript_tool.run(input_data)

@patch.object(YouTubeTranscriptApi, 'get_transcript')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.fetch_video_metadata')
@patch('atomic_agents.lib.tools.yt_transcript_scraper.YouTubeTranscriptTool.extract_video_id')
def test_run_transcripts_disabled(mock_extract_video_id, mock_fetch_metadata, mock_get_transcript, youtube_transcript_tool):
    mock_extract_video_id.return_value = "dQw4w9WgXcQ"
    mock_fetch_metadata.return_value = SAMPLE_VIDEO_INFO
    mock_get_transcript.side_effect = TranscriptsDisabled("Transcripts are disabled for this video")
    
    input_data = YouTubeTranscriptToolSchema(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    with pytest.raises(Exception, match="Failed to fetch transcript for video 'dQw4w9WgXcQ': "):
        youtube_transcript_tool.run(input_data)

@patch('atomic_agents.lib.tools.yt_transcript_scraper.build')
def test_fetch_video_metadata_success(mock_build, youtube_transcript_tool):
    mock_youtube = Mock()
    mock_build.return_value = mock_youtube
    mock_request = Mock()
    mock_youtube.videos().list.return_value = mock_request
    mock_request.execute.return_value = {
        "items": [
            {
                "snippet": {
                    "title": "Sample Video",
                    "channelTitle": "Sample Channel",
                    "publishedAt": "2023-01-01T00:00:00Z",
                }
            }
        ]
    }

    video_id = "dQw4w9WgXcQ"
    metadata = youtube_transcript_tool.fetch_video_metadata(video_id)

    assert metadata == {
        "id": video_id,
        "title": "Sample Video",
        "channel": "Sample Channel",
        "published_at": "2023-01-01T00:00:00Z",
    }
    mock_build.assert_called_once_with("youtube", "v3", developerKey=youtube_transcript_tool.api_key)
    mock_youtube.videos().list.assert_called_once_with(part="snippet", id=video_id)

@patch('atomic_agents.lib.tools.yt_transcript_scraper.build')
def test_fetch_video_metadata_no_items(mock_build, youtube_transcript_tool):
    mock_youtube = Mock()
    mock_build.return_value = mock_youtube
    mock_request = Mock()
    mock_youtube.videos().list.return_value = mock_request
    mock_request.execute.return_value = {"items": []}

    video_id = "dQw4w9WgXcQ"

    with pytest.raises(Exception, match=f"No metadata found for video '{video_id}'"):
        youtube_transcript_tool.fetch_video_metadata(video_id)

    mock_build.assert_called_once_with("youtube", "v3", developerKey=youtube_transcript_tool.api_key)
    mock_youtube.videos().list.assert_called_once_with(part="snippet", id=video_id)
