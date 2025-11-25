# Basic PDF Analysis Example

This example demonstrates how to use the Atomic Agents framework to analyze a PDF file, using Google generative AI's multimodal capabilities.

## Features

1. PDF document analysis: Process a PDF document using Google generative AI multimodal capability.
2. Structured Data Extraction: Extract key information from PDFs into a structured Pydantic model:
   - Document title
   - Page count

## Getting Started

1. Clone the main Atomic Agents repository:
   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. Navigate to the basic-pdf-analysis directory:
   ```bash
   cd atomic-agents/atomic-examples/basic-pdf-analysis
   ```

3. Install dependencies using uv:
   ```bash
   uv sync
   ```

4. Set up environment variables:
   Create a `.env` file in the `basic-pdf-analysis` directory with the following content:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   ```
   Replace `your_gemini_api_key` with your actual google generative AI key.

5. Run the example:
   ```bash
   uv run python basic_pdf_analysis/main.py
   ```

## Components

### 1. Input/Output Schemas
- `InputSchema`: Handles the input PDF file
- `ExtractionResult`: Structures the extracted information

### 2. Agent
A specialized agent configured with:
- Google generative AI gemini-2.0-flash model
- Custom system prompt
- Structured data validation

## Example Usage

The example includes a test PDF file in the `test_media` directory.

Running the example will:
1. Load the PDF from the `test_media` directory
2. Process it with the agent
3. Display the extracted information:
   - PDF title
   - Page count

Example output:
```
Starting PDF file analysis...
Analyzing PDF file: pdf_sample.pdf ...

===== Analysis Results =====
PDF Title: Sample PDF Document
Page Count: 3
Document summary: This PDF is three pages long and contains Latin text.

Analysis completed successfully
```

## Customization

You can modify the example by:
1. Adding your own files to the `test_media` directory
2. Adjusting the `ExtractionResult` schema to capture additional information
3. Modifying the system prompts to extract different or additional information

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](../../LICENSE) file for details.
