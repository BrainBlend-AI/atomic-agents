# Yt Transcript Scraper Tool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / Yt Transcript Scraper Tool

> Auto-generated documentation for [atomic_agents.lib.tools.yt_transcript_scraper_tool](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py) module.

- [Yt Transcript Scraper Tool](#yt-transcript-scraper-tool)
  - [YouTubeTranscriptTool](#youtubetranscripttool)
    - [YouTubeTranscriptTool.extract_video_id](#youtubetranscripttoolextract_video_id)
    - [YouTubeTranscriptTool().fetch_video_metadata](#youtubetranscripttool()fetch_video_metadata)
    - [YouTubeTranscriptTool().run](#youtubetranscripttool()run)
  - [YouTubeTranscriptToolConfig](#youtubetranscripttoolconfig)
  - [YouTubeTranscriptToolInputSchema](#youtubetranscripttoolinputschema)
  - [YouTubeTranscriptToolOutputSchema](#youtubetranscripttooloutputschema)

## YouTubeTranscriptTool

[Show source in yt_transcript_scraper_tool.py:59](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py#L59)

Tool for fetching the transcript of a YouTube video using the YouTube Transcript API.

#### Attributes

- `input_schema` *YouTubeTranscriptToolInputSchema* - The schema for the input data.
- `output_schema` *YouTubeTranscriptToolOutputSchema* - The schema for the output data.

#### Signature

```python
class YouTubeTranscriptTool(BaseTool):
    def __init__(self, config: YouTubeTranscriptToolConfig): ...
```

#### See also

- [BaseTool](./base_tool.md#basetool)
- [YouTubeTranscriptToolConfig](#youtubetranscripttoolconfig)

### YouTubeTranscriptTool.extract_video_id

[Show source in yt_transcript_scraper_tool.py:115](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py#L115)

Extracts the video ID from a YouTube URL.

#### Arguments

- `url` *str* - The YouTube video URL.

#### Returns

- `str` - The extracted video ID.

#### Signature

```python
@staticmethod
def extract_video_id(url: str) -> str: ...
```

### YouTubeTranscriptTool().fetch_video_metadata

[Show source in yt_transcript_scraper_tool.py:128](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py#L128)

Fetches metadata for a YouTube video.

#### Arguments

- `video_id` *str* - The YouTube video ID.

#### Returns

- `dict` - The metadata of the video.

#### Signature

```python
def fetch_video_metadata(self, video_id: str) -> dict: ...
```

### YouTubeTranscriptTool().run

[Show source in yt_transcript_scraper_tool.py:81](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py#L81)

Runs the YouTubeTranscriptTool with the given parameters.

#### Arguments

- `params` *YouTubeTranscriptToolInputSchema* - The input parameters for the tool, adhering to the input schema.

#### Returns

- [YouTubeTranscriptToolOutputSchema](#youtubetranscripttooloutputschema) - The output of the tool, adhering to the output schema.

#### Raises

- `Exception` - If fetching the transcript fails.

#### Signature

```python
def run(
    self, params: YouTubeTranscriptToolInputSchema
) -> YouTubeTranscriptToolOutputSchema: ...
```

#### See also

- [YouTubeTranscriptToolInputSchema](#youtubetranscripttoolinputschema)
- [YouTubeTranscriptToolOutputSchema](#youtubetranscripttooloutputschema)



## YouTubeTranscriptToolConfig

[Show source in yt_transcript_scraper_tool.py:52](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py#L52)

#### Signature

```python
class YouTubeTranscriptToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base_tool.md#basetoolconfig)



## YouTubeTranscriptToolInputSchema

[Show source in yt_transcript_scraper_tool.py:17](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py#L17)

#### Signature

```python
class YouTubeTranscriptToolInputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](../../agents/base_agent.md#baseioschema)



## YouTubeTranscriptToolOutputSchema

[Show source in yt_transcript_scraper_tool.py:35](../../../../../atomic_agents/lib/tools/yt_transcript_scraper_tool.py#L35)

#### Signature

```python
class YouTubeTranscriptToolOutputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](../../agents/base_agent.md#baseioschema)