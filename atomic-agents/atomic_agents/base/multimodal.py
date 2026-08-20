"""Multimodal content types that Instructor does not provide."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VideoURL(BaseModel):
    """
    Video reference sent to the LLM as an OpenAI-compatible ``video_url`` content part.

    Instructor ships Image, Audio, and PDF types but no video type
    (see https://github.com/567-labs/instructor/discussions/2520), so this class fills
    the gap for providers that accept ``video_url`` content parts, such as MiniMax
    and Qwen-VL.

    Attributes:
        url (str): HTTP(S) or data: URL of the video.
        fps (Optional[float]): Frame sampling rate, for providers that accept it.
        detail (Optional[str]): Detail level, for providers that accept it.
    """

    url: str = Field(..., description="HTTP(S) or data: URL of the video.")
    fps: Optional[float] = Field(default=None, description="Frame sampling rate, for providers that accept it.")
    detail: Optional[str] = Field(default=None, description="Detail level, for providers that accept it.")

    def to_openai(self) -> Dict[str, Any]:
        """
        Build the OpenAI-compatible content part for this video.

        Returns:
            Dict[str, Any]: A ``{"type": "video_url", "video_url": {...}}`` content part,
            omitting optional parameters that were not set.
        """
        return {"type": "video_url", "video_url": self.model_dump(exclude_none=True)}
