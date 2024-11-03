# Deep Research Agent

This directory contains the Deep Research Agent example for the Atomic Agents project. This example demonstrates how to create an intelligent research assistant that performs web searches and provides detailed answers with relevant follow-up questions.

## Getting Started

1. **Clone the main Atomic Agents repository:**
   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. **Navigate to the Deep Research directory:**
   ```bash
   cd atomic-agents/atomic-examples/deep-research
   ```

3. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```

4. **Set up environment variables:**
   Create a `.env` file in the `deep-research` directory with:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```

5. **Set up SearxNG:**
   - Install SearxNG from the [official repository](https://github.com/searxng/searxng)
   - Default configuration expects SearxNG at `http://localhost:8080`

6. **Run the Deep Research Agent:**
   ```bash
   poetry run python deep_research/main.py
   ```

## File Explanation

### 1. Agents (`agents/`)

- **ChoiceAgent** (`choice_agent.py`): Determines when new searches are needed
- **QueryAgent** (`query_agent.py`): Generates optimized search queries
- **QuestionAnsweringAgent** (`qa_agent.py`): Processes information and generates responses

### 2. Tools (`tools/`)

- **SearxNG Search** (`searxng_search.py`): Performs web searches across multiple engines
- **Webpage Scraper** (`webpage_scraper.py`): Extracts and processes web content

### 3. Main (`main.py`)

The entry point for the Deep Research Agent application. It orchestrates the research process:
- Deciding when to perform new searches
- Generating and executing search queries
- Processing information and providing answers
- Suggesting relevant follow-up questions

## Example Usage

The agent can handle various research queries and provides:
- Detailed answers based on current web information
- Relevant citations and sources
- Specific follow-up questions for deeper exploration
- Context-aware responses that build on previous interactions

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](../../LICENSE) file for details.
