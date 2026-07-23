import os
import sys
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api import (
    FetchedTranscript,
    FetchedTranscriptSnippet,
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

# Add the parent directory of 'tests' to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tool.youtube_transcript_scraper import (  # noqa: E402
    YouTubeTranscriptTool,
    YouTubeTranscriptToolConfig,
    YouTubeTranscriptToolInputSchema,
    YouTubeTranscriptToolOutputSchema,
)


def make_fetched_transcript():
    return FetchedTranscript(
        snippets=[
            FetchedTranscriptSnippet(text="Never gonna give you up", start=0.0, duration=5.0),
            FetchedTranscriptSnippet(text="Never gonna let you down", start=5.0, duration=5.0),
        ],
        video_id="dQw4w9WgXcQ",
        language="English",
        language_code="en",
        is_generated=False,
    )


@contextmanager
def mock_transcript_api(fetched_transcript=None, side_effect=None):
    api = MagicMock(spec=YouTubeTranscriptApi)
    api.fetch = MagicMock(return_value=fetched_transcript, side_effect=side_effect)

    def fetch_raw_transcript(video_id, languages=None):
        if languages is None:
            fetched = api.fetch(video_id)
        else:
            fetched = api.fetch(video_id, languages=languages)
        return fetched.to_raw_data()

    api.get_transcript = fetch_raw_transcript
    with patch("tool.youtube_transcript_scraper.YouTubeTranscriptApi", api):
        yield api


def test_youtube_transcript_tool():
    mock_api_key = "mock_api_key"
    mock_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_video_id = "dQw4w9WgXcQ"
    mock_metadata = {
        "title": "Rick Astley - Never Gonna Give You Up",
        "channelTitle": "Rick Astley",
        "publishedAt": "2009-10-25T06:57:33Z",
    }

    with (
        mock_transcript_api(make_fetched_transcript()) as mock_transcript_api_instance,
        patch("tool.youtube_transcript_scraper.build") as mock_build,
    ):
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.videos().list().execute.return_value = {"items": [{"snippet": mock_metadata}]}

        youtube_transcript_tool = YouTubeTranscriptTool(YouTubeTranscriptToolConfig(api_key=mock_api_key))
        input_schema = YouTubeTranscriptToolInputSchema(video_url=mock_video_url)
        result = youtube_transcript_tool.run(input_schema)

        assert isinstance(result, YouTubeTranscriptToolOutputSchema)
        assert result.transcript == "Never gonna give you up Never gonna let you down"
        assert result.duration == 10.0
        assert result.comments == []
        assert result.metadata.model_dump() == {
            "id": mock_video_id,
            "title": mock_metadata["title"],
            "channel": mock_metadata["channelTitle"],
            "published_at": datetime.fromisoformat(mock_metadata["publishedAt"].replace("Z", "")),
        }
        mock_transcript_api_instance.fetch.assert_called_once_with(mock_video_id)


def test_youtube_transcript_tool_with_language():
    mock_api_key = "mock_api_key"
    mock_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_video_id = "dQw4w9WgXcQ"
    mock_metadata = {
        "title": "Rick Astley - Never Gonna Give You Up",
        "channelTitle": "Rick Astley",
        "publishedAt": "2009-10-25T06:57:33Z",
    }

    with (
        mock_transcript_api(make_fetched_transcript()) as mock_transcript_api_instance,
        patch("tool.youtube_transcript_scraper.build") as mock_build,
    ):
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.videos().list().execute.return_value = {"items": [{"snippet": mock_metadata}]}

        youtube_transcript_tool = YouTubeTranscriptTool(YouTubeTranscriptToolConfig(api_key=mock_api_key))
        input_schema = YouTubeTranscriptToolInputSchema(video_url=mock_video_url, language="en")
        result = youtube_transcript_tool.run(input_schema)

        assert isinstance(result, YouTubeTranscriptToolOutputSchema)
        assert result.transcript == "Never gonna give you up Never gonna let you down"
        mock_transcript_api_instance.fetch.assert_called_once_with(mock_video_id, languages=["en"])


def test_youtube_transcript_tool_no_transcript():
    mock_api_key = "mock_api_key"
    mock_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    with mock_transcript_api(
        side_effect=NoTranscriptFound(
            video_id="dQw4w9WgXcQ",
            requested_language_codes=["en"],
            transcript_data=None,
        )
    ):
        youtube_transcript_tool = YouTubeTranscriptTool(YouTubeTranscriptToolConfig(api_key=mock_api_key))
        input_schema = YouTubeTranscriptToolInputSchema(video_url=mock_video_url)

        with pytest.raises(Exception) as excinfo:
            youtube_transcript_tool.run(input_schema)

        assert "Failed to fetch transcript" in str(excinfo.value)


def test_youtube_transcript_tool_transcripts_disabled():
    mock_api_key = "mock_api_key"
    mock_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    with mock_transcript_api(side_effect=TranscriptsDisabled("Transcripts are disabled")):
        youtube_transcript_tool = YouTubeTranscriptTool(YouTubeTranscriptToolConfig(api_key=mock_api_key))
        input_schema = YouTubeTranscriptToolInputSchema(video_url=mock_video_url)

        with pytest.raises(Exception) as excinfo:
            youtube_transcript_tool.run(input_schema)

        assert "Failed to fetch transcript" in str(excinfo.value)


def test_fetch_video_metadata_no_items():
    mock_api_key = "mock_api_key"

    with patch("tool.youtube_transcript_scraper.build") as mock_build:
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.videos().list().execute.return_value = {"items": []}

        youtube_transcript_tool = YouTubeTranscriptTool(YouTubeTranscriptToolConfig(api_key=mock_api_key))

        with pytest.raises(Exception) as excinfo:
            youtube_transcript_tool.fetch_video_metadata("dQw4w9WgXcQ")

        assert "No metadata found for video" in str(excinfo.value)


def test_extract_video_id():
    youtube_transcript_tool = YouTubeTranscriptTool(YouTubeTranscriptToolConfig(api_key="mock_api_key"))
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_id = youtube_transcript_tool.extract_video_id(video_url)
    assert video_id == "dQw4w9WgXcQ"


if __name__ == "__main__":
    pytest.main([__file__])
