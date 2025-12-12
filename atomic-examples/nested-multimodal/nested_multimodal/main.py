"""
Nested Multimodal Content Example

This example demonstrates the support for nested multimodal content in Atomic Agents,
as implemented for GitHub Issue #141: "AgentMemory: support nested multimodal data"

The key scenario demonstrated here is:
- A Document schema containing an Image field AND metadata (owner)
- An InputSchema containing a LIST of Documents
- The agent correctly processes all nested Images and extracts information from each

Previously, nested multimodal content like this would be incorrectly serialized with json.dumps,
causing issues. Now the ChatHistory recursively detects and extracts multimodal content at any depth.

This example supports both:
- OpenAI (GPT-5.1) with OPENAI_API_KEY
- Google Gemini with GEMINI_API_KEY
"""

import os
from pathlib import Path
from typing import List

import instructor
from openai import OpenAI
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator
from instructor.processing.multimodal import Image
from pydantic import Field


def _load_env():
    """Load .env file from current or parent directories."""
    for directory in [Path.cwd(), *Path.cwd().parents]:
        env_file = directory / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
            break


_load_env()


# =============================================================================
# Schema Definitions - Demonstrating Nested Multimodal Content (Issue #141)
# =============================================================================


class ImageDocument(BaseIOSchema):
    """
    A document with Image content and metadata.

    This is the KEY nested structure - the Image is inside this schema,
    not at the top level of the InputSchema.
    """

    image: Image = Field(..., description="The image content")
    owner: str = Field(..., description="The owner/author of this image")
    category: str = Field(..., description="Category of the image (e.g., 'logo', 'photo', 'diagram')")


class NestedMultimodalInput(BaseIOSchema):
    """
    Input schema with nested multimodal content.

    This demonstrates Issue #141 - multimodal content (Images) nested within
    a list of ImageDocument objects, not at the top level.
    """

    documents: List[ImageDocument] = Field(..., description="List of image documents to analyze")
    analysis_query: str = Field(..., description="What to analyze or compare across the images")


class ImageAnalysis(BaseIOSchema):
    """Analysis result for a single image document."""

    owner: str = Field(..., description="The owner of this image")
    category: str = Field(..., description="The category of the image")
    description: str = Field(..., description="Description of what's in the image")
    dominant_colors: List[str] = Field(..., description="Main colors visible in the image")
    key_elements: List[str] = Field(..., description="Key visual elements identified")


class AnalysisResult(BaseIOSchema):
    """Combined analysis of all image documents."""

    image_analyses: List[ImageAnalysis] = Field(..., description="Analysis of each individual image")
    comparative_summary: str = Field(..., description="Comparative analysis addressing the user's query")


# =============================================================================
# Agent Setup with Provider Auto-Detection
# =============================================================================


def create_agent():
    """Create the image analysis agent with auto-detected provider."""

    # Try OpenAI first, then Gemini
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if openai_key:
        print("Using OpenAI GPT-5.1")
        client = instructor.from_openai(OpenAI(api_key=openai_key))
        model = "gpt-5.1"
    elif gemini_key:
        print("Using Google Gemini")
        from google import genai

        client = instructor.from_genai(client=genai.Client(api_key=gemini_key), mode=instructor.Mode.GENAI_TOOLS)
        model = "gemini-2.0-flash"
    else:
        raise ValueError("No API key found. Please set OPENAI_API_KEY or GEMINI_API_KEY in your .env file.")

    system_prompt_generator = SystemPromptGenerator(
        background=[
            "You are an image analysis expert.",
            "You can analyze multiple images and provide comparative insights.",
        ],
        steps=[
            "For each image document in the input, analyze and describe what you see.",
            "Consider the owner and category metadata provided for each image.",
            "Identify key visual elements, colors, and notable features.",
            "After analyzing all images, provide a comparative summary based on the user's query.",
        ],
        output_instructions=[
            "Return detailed analysis for each image.",
            "Include a comparative summary that addresses the user's specific query.",
        ],
    )

    agent = AtomicAgent[NestedMultimodalInput, AnalysisResult](
        config=AgentConfig(
            client=client,
            model=model,
            system_prompt_generator=system_prompt_generator,
            input_schema=NestedMultimodalInput,
            output_schema=AnalysisResult,
        )
    )

    return agent


def main():
    """
    Main function demonstrating nested multimodal content handling.

    This creates multiple ImageDocument objects, each containing an Image,
    and passes them as a list to the agent - the exact scenario from Issue #141.
    """
    print("=" * 60)
    print("Nested Multimodal Content Example (Issue #141)")
    print("=" * 60)
    print()

    # Get the test image paths
    script_directory = os.path.dirname(os.path.abspath(__file__))
    test_media_directory = os.path.join(os.path.dirname(script_directory), "test_media")
    image_path1 = os.path.join(test_media_directory, "image_sample.jpg")
    image_path2 = os.path.join(test_media_directory, "image_sample2.jpg")

    # Check for test images
    if not os.path.exists(image_path1) or not os.path.exists(image_path2):
        print(f"Error: Test images not found in {test_media_directory}")
        print("Please ensure image_sample.jpg and image_sample2.jpg exist.")
        return

    print(f"Using test images from: {test_media_directory}")
    print()

    # Create the agent
    try:
        agent = create_agent()
    except ValueError as e:
        print(f"Setup error: {e}")
        return

    print()

    # ==========================================================================
    # KEY DEMONSTRATION: Nested multimodal content
    # ==========================================================================
    # We create MULTIPLE ImageDocument objects, each containing an Image.
    # This is the exact scenario from Issue #141 that wasn't working before.
    # The Images are nested inside ImageDocument schemas, inside a list.

    print("Creating nested document structure...")
    print("  - Document 1: Image owned by 'Marketing Team', category 'random photo'")
    print("  - Document 2: Image owned by 'Content Team', category 'random photo'")
    print()

    document1 = ImageDocument(image=Image.from_path(image_path1), owner="Marketing Team", category="random photo")
    document2 = ImageDocument(image=Image.from_path(image_path2), owner="Content Team", category="random photo")

    # Create the nested input - this is what Issue #141 fixed
    nested_input = NestedMultimodalInput(
        documents=[document1, document2],
        analysis_query="Compare these images and describe what you see in each one. Note any similarities or differences.",
    )

    print("Sending nested multimodal content to agent...")
    print("(Previously this would fail due to incorrect JSON serialization)")
    print()

    try:
        # Run the agent with nested multimodal content
        result = agent.run(nested_input)

        # Display results
        print("=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        print()

        for i, img_analysis in enumerate(result.image_analyses, 1):
            print(f"Image {i}:")
            print(f"  Owner: {img_analysis.owner}")
            print(f"  Category: {img_analysis.category}")
            print(f"  Description: {img_analysis.description}")
            print(f"  Dominant Colors: {', '.join(img_analysis.dominant_colors)}")
            print(f"  Key Elements: {', '.join(img_analysis.key_elements)}")
            print()

        print("Comparative Summary:")
        print(f"  {result.comparative_summary}")
        print()

        print("=" * 60)
        print("SUCCESS: Nested multimodal content handled correctly!")
        print("=" * 60)

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
