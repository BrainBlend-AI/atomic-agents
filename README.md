# Atomic Agents Redux

## Description

Atomic Agents Redux is a versatile framework designed to facilitate the creation and management of intelligent agents. These agents can perform a variety of tasks, including web scraping, calculations, and generating article ideas with integrated search capabilities. The project leverages powerful models like GPT-3.5-turbo to provide intelligent responses and perform complex operations.

## Installation

To install the necessary dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Usage

### Base Chat Agent

The `BaseChatAgent` class is the core component of the framework. It handles user input, generates system prompts, and retrieves responses from the model.

Example usage:

```python
from atomic_agents.agents.base_chat_agent import BaseChatAgent
from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
import instructor
import openai

client = instructor.from_openai(openai.OpenAI(api_key="your_openai_api_key"))
memory = ChatMemory()
system_prompt_generator = SystemPromptGenerator()

agent = BaseChatAgent(client=client, system_prompt_generator=system_prompt_generator, memory=memory)
response = agent.run("Hello, how can you assist me today?")
print(response)
```

### Web Scraping Tool

The `WebScrapingTool` class allows you to scrape web pages and convert their content to markdown format.

Example usage:

```python
from atomic_agents.lib.tools.web_scraping_tool import WebScrapingTool, WebScrapingToolSchema

tool = WebScrapingTool()
params = WebScrapingToolSchema(url="https://example.com")
result = tool.run(params)
print(result.result.content)
```

### Calculator Tool

The `CalculatorTool` class evaluates mathematical expressions.

Example usage:

```python
from atomic_agents.lib.tools.calculator_tool import CalculatorTool, CalculatorToolSchema

tool = CalculatorTool()
params = CalculatorToolSchema(expression="2 + 2")
result = tool.run(params)
print(result.result)
```

### SearxNG Search Tool

The `SearxNGSearchTool` class performs searches using the SearxNG search engine.

Example usage:

```python
from atomic_agents.lib.tools.searx import SearxNGSearchTool, SearxNGSearchToolSchema

tool = SearxNGSearchTool(max_results=10)
params = SearxNGSearchToolSchema(queries=["latest news", "technology trends"])
result = tool.run(params)
for res in result.results:
    print(f"Title: {res.title}, URL: {res.url}")
```

### Article Idea Outline Generator with Search

The `article_idea_outline_gen_with_search.py` script demonstrates how to use the framework to generate article ideas and outlines with integrated search capabilities.

Example usage:

```python
from atomic_agents.examples.article_idea_outline_gen_with_search import MyChatAgent
import instructor
import openai

client = instructor.from_openai(openai.OpenAI(api_key="your_openai_api_key"))
agent = MyChatAgent(client=client)
response = agent.run("Generate article ideas about AI in healthcare.")
print(response)
```

## Contributing

We welcome contributions! Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Open a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.