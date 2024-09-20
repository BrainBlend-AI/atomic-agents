# YouTube Transcript Scraper Tool

## Overview
The YouTube Transcript Scraper Tool is a Python-based utility designed for fetching and processing transcripts from YouTube videos. It uses the YouTube Transcript API to retrieve transcripts and the Google API to fetch video metadata. This tool is built using the Pydantic library for input validation and leverages the `atomic_agents` framework for consistent tool structure.

## Features
- Fetch transcripts from YouTube videos.
- Support for language-specific transcript retrieval.
- Retrieve video metadata (title, channel, publication date).
- Input validation using Pydantic.
- Error handling for common transcript fetching issues.

## Example Usage

```python
from tool.youtube_transcript_scraper import YouTubeTranscriptTool, YouTubeTranscriptToolConfig

api_key = "your_youtube_api_key"
transcript_tool = YouTubeTranscriptTool(config=YouTubeTranscriptToolConfig(api_key=api_key))

input_data = YouTubeTranscriptTool.input_schema(
    video_url="https://www.youtube.com/watch?v=t1e8gqXLbsU",
    language="en"
)

result = transcript_tool.run(input_data)
print(result)  # Output: YouTubeTranscriptToolOutputSchema with transcript, duration, and metadata
```
