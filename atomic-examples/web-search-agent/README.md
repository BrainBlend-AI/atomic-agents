# Web Search Agent

This project demonstrates an intelligent web search agent built using the Atomic Agents framework. The agent can perform web searches, generate relevant queries, and provide detailed answers to user questions based on the search results.

## Features

1. Query Generation: Automatically generates relevant search queries based on user input.
2. Web Search: Utilizes SearxNG to perform web searches across multiple search engines.
3. Question Answering: Provides detailed answers to user questions based on search results.
4. Follow-up Questions: Suggests related questions to encourage further exploration of the topic.

## Components

The Web Search Agent consists of several key components:

1. Query Agent (`query_agent.py`): Generates diverse and relevant search queries based on user input.
2. SearxNG Search Tool (`searxng_search.py`): Performs web searches using the SearxNG meta-search engine.
3. Question Answering Agent (`question_answering_agent.py`): Analyzes search results and provides detailed answers to user questions.
4. Main Script (`main.py`): Orchestrates the entire process, from query generation to final answer presentation.

## Getting Started

To run the Web Search Agent:

1. Clone the Atomic Agents repository:
   ```
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. Navigate to the web-search-agent directory:
   ```
   cd atomic-agents/atomic-examples/web-search-agent
   ```

3. Install dependencies using Poetry:
   ```
   poetry install
   ```

4. Set up environment variables:
   Create a `.env` file in the `web-search-agent` directory with the following content:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SEARXNG_BASE_URL=your_searxng_instance_url
   ```
   Replace `your_openai_api_key` with your actual OpenAI API key and `your_searxng_instance_url` with the URL of your SearxNG instance.

5. Run the Web Search Agent:
   ```
   poetry run python web_search_agent/main.py
   ```

## How It Works

1. The user provides an initial question or topic for research.
2. The Query Agent generates multiple relevant search queries based on the user's input.
3. The SearxNG Search Tool performs web searches using the generated queries.
4. The Question Answering Agent analyzes the search results and formulates a detailed answer.
5. The main script presents the answer, along with references and follow-up questions.

## Customization

You can customize the Web Search Agent by modifying the following:

- Adjust the number of generated queries in `main.py`.
- Modify the search categories or parameters in `searxng_search.py`.
- Customize the system prompts for the Query Agent and Question Answering Agent in their respective files.

## Contributing

Contributions to the Web Search Agent project are welcome! Please fork the repository and submit a pull request with your enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](../../LICENSE) file for details.

