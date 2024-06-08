# Yt Transcript Scraper

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / Yt Transcript Scraper

> Auto-generated documentation for [atomic_agents.lib.tools.yt_transcript_scraper](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py) module.

- [Yt Transcript Scraper](#yt-transcript-scraper)
  - [YouTubeTranscriptResultSchema](#youtubetranscriptresultschema)
  - [YouTubeTranscriptTool](#youtubetranscripttool)
    - [YouTubeTranscriptTool.extract_video_id](#youtubetranscripttoolextract_video_id)
    - [YouTubeTranscriptTool().fetch_video_metadata](#youtubetranscripttool()fetch_video_metadata)
    - [YouTubeTranscriptTool().run](#youtubetranscripttool()run)
  - [YouTubeTranscriptToolConfig](#youtubetranscripttoolconfig)
  - [YouTubeTranscriptToolOutputSchema](#youtubetranscripttooloutputschema)
  - [YouTubeTranscriptToolSchema](#youtubetranscripttoolschema)

## YouTubeTranscriptResultSchema

[Show source in yt_transcript_scraper.py:27](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L27)

#### Signature

```python
class YouTubeTranscriptResultSchema(BaseModel): ...
```



## YouTubeTranscriptTool

[Show source in yt_transcript_scraper.py:44](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L44)

Tool for fetching the transcript of a YouTube video using the YouTube Transcript API.

#### Attributes

- `input_schema` *YouTubeTranscriptToolSchema* - The schema for the input data.
- `output_schema` *YouTubeTranscriptToolOutputSchema* - The schema for the output data.

#### Signature

```python
class YouTubeTranscriptTool(BaseTool):
    def __init__(self, config: YouTubeTranscriptToolConfig): ...
```

#### See also

- [BaseTool](./base.md#basetool)
- [YouTubeTranscriptToolConfig](#youtubetranscripttoolconfig)

### YouTubeTranscriptTool.extract_video_id

[Show source in yt_transcript_scraper.py:99](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L99)

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

[Show source in yt_transcript_scraper.py:112](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L112)

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

[Show source in yt_transcript_scraper.py:65](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L65)

Runs the YouTubeTranscriptTool with the given parameters.

#### Arguments

- `params` *YouTubeTranscriptToolSchema* - The input parameters for the tool, adhering to the input schema.

#### Returns

- [YouTubeTranscriptToolOutputSchema](#youtubetranscripttooloutputschema) - The output of the tool, adhering to the output schema.

#### Raises

- `Exception` - If fetching the transcript fails.

#### Signature

```python
def run(
    self, params: YouTubeTranscriptToolSchema
) -> YouTubeTranscriptToolOutputSchema: ...
```

#### See also

- [YouTubeTranscriptToolOutputSchema](#youtubetranscripttooloutputschema)
- [YouTubeTranscriptToolSchema](#youtubetranscripttoolschema)



## YouTubeTranscriptToolConfig

[Show source in yt_transcript_scraper.py:41](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L41)

#### Signature

```python
class YouTubeTranscriptToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base.md#basetoolconfig)



## YouTubeTranscriptToolOutputSchema

[Show source in yt_transcript_scraper.py:32](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L32)

#### Signature

```python
class YouTubeTranscriptToolOutputSchema(BaseModel): ...
```



## YouTubeTranscriptToolSchema

[Show source in yt_transcript_scraper.py:12](../../../../../atomic_agents/lib/tools/yt_transcript_scraper.py#L12)

#### Signature

```python
class YouTubeTranscriptToolSchema(BaseModel): ...
```