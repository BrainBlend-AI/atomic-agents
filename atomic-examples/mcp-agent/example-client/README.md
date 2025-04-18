# MCP Agent Example

This example demonstrates how to choose the right MCP tool for a user query using the MCP Tool Factory. It showcases:

- Dynamic discovery of available MCP tools
- Intelligent tool selection using gpt-4o-mini
- Parameter extraction from natural language queries
- Tool execution with extracted parameters
- Pretty output formatting using Rich

## Features

- **Tool Discovery**: Automatically fetches all available tools from the MCP server
- **Smart Selection**: Uses gpt-4o-mini to understand user queries and select the most appropriate tool
- **Parameter Extraction**: Extracts tool parameters directly from natural language queries
- **Fallback Generation**: Generates random input if parameters cannot be extracted
- **Rich Output**: Beautiful console output with colors and tables

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key
   ```

3. Ensure the MCP server is running at `http://localhost:6969`

## Usage

Run the example:
```bash
poetry run python main.py
```

The script will:
1. Fetch all available MCP tools
2. Display them in a table
3. Process example queries, selecting the right tool and extracting parameters
4. Execute each tool and display the results

## Tool Selection Logic

The example uses gpt-4o-mini for two key tasks:

1. **Tool Selection**: Given a user query and list of available tools, the model selects the most appropriate tool with a confidence score.

2. **Parameter Extraction**: For the selected tool, the model extracts relevant parameters from the query.

If parameter extraction fails, the script falls back to generating random input.

## Example Queries

The script includes several example queries that demonstrate different capabilities:

- "Please add the numbers 69 and 420"
- "Can you reverse this string: 'hello world'"
- "What is the current time?"
- "Calculate the difference between 2025-04-05 and 2025-04-15"
- "Generate a random number between 10 and 100"

## Extending

To add your own queries or tools:

1. Modify the `example_queries` list in `main.py`
2. Add new tools to your MCP server
3. The script will automatically discover and use new tools

## Requirements

- Python 3.9+
- MCP server running at `http://localhost:6969`
- OpenAI API key for gpt-4o-mini
- Poetry for dependency management

---

**This example is intended for educational and demonstration purposes.**
