import os

import instructor
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator
from dotenv import load_dotenv
from google import genai
from instructor.multimodal import PDF
from pydantic import Field


load_dotenv()


class InputSchema(BaseIOSchema):
    """PDF file to analyze."""

    pdf: PDF = Field(..., description="The PDF data")  # PDF class from instructor


class ExtractionResult(BaseIOSchema):
    """Extracted information from the PDF."""

    pdf_title: str = Field(..., description="The title of the PDF file")
    page_count: int = Field(..., description="The number of pages in the PDF file")
    summary: str = Field(..., description="A short summary of the document")


# Define the LLM CLient using GenAI instructor wrapper:
client = instructor.from_genai(client=genai.Client(api_key=os.getenv("GEMINI_API_KEY")), mode=instructor.Mode.GENAI_TOOLS)

# Define the system prompt:
system_prompt_generator = SystemPromptGenerator(
    background=["You are a helpful assistant that extracts information from PDF files."],
    steps=[
        "Analyze the PDF, extract its title and count the number of pages.",
        "Create a brief summary of the document content.",
    ],
    output_instructions=["Return pdf_title, page_count, and summary."],
)

# Define the agent
agent = AtomicAgent[InputSchema, ExtractionResult](
    config=AgentConfig(
        client=client,
        model="gemini-2.0-flash",
        system_prompt_generator=system_prompt_generator,
        input_schema=InputSchema,
        output_schema=ExtractionResult,
    )
)


def main():
    print("Starting PDF file analysis...")

    # Create the analysis request
    script_directory = os.path.dirname(os.path.abspath(__file__))
    test_media_directory = os.path.join(os.path.dirname(script_directory), "test_media")
    pdf_path = os.path.join(test_media_directory, "pdf_sample.pdf")
    analysis_request = InputSchema(
        pdf=PDF.from_path(pdf_path),
    )

    try:
        # Process the PDF file
        print(f"Analyzing PDF file: {os.path.basename(pdf_path)} ...")
        analysis_result = agent.run(analysis_request)

        # Display the results
        print("\n===== Analysis Results =====")
        print(f"PDF Title: {analysis_result.pdf_title}")
        print(f"Page Count: {analysis_result.page_count}")
        print(f"Document summary: {analysis_result.summary}")

    except Exception as e:
        print(f"Analysis failed: {str(e)}")
        raise e


if __name__ == "__main__":
    main()
