# Atomic Agents
<img src="./.assets/logo.png" alt="Atomic Agents" width="350"/>

[![PyPI version](https://badge.fury.io/py/atomic-agents.svg)](https://badge.fury.io/py/atomic-agents)

## Philosophy
The Atomic Agents framework is designed to be modular, extensible, and easy to use. Components in the Atomic Agents Framework should always be as small and single-purpose as possible, similar to design system components in [Atomic Design](https://bradfrost.com/blog/post/atomic-web-design/). Even though Atomic Design cannot be directly applied to AI agent architecture, a lot of ideas were taken from it. The resulting framework provides a set of tools and agents that can be combined to create powerful applications. The framework is built on top of [Instructor](https://github.com/jxnl/instructor) and leverages the power of [Pydantic](https://docs.pydantic.dev/latest/) for data validation and serialization.

<!-- ![alt text](./.assets/architecture_highlevel_overview.png) -->
<img src="./.assets/architecture_highlevel_overview.png" alt="Atomic Agents Architecture" width="600"/>
<img src="./.assets/what_is_sent_in_prompt.png" alt="What is sent to the LLM in the prompt?" width="600"/>

## Installation
To install Atomic Agents, you can use pip:

```bash
pip install atomic-agents
```

Alternatively, to install the necessary dependencies from the repository, run the following command:

```bash
python -m venv venv
source venv/bin/activate # On Windows, use `venv\Scripts\activate.bat`
pip install -r requirements.txt
pip install -e .
```

## Quickstart
A quickstart guide is available in the [quickstart notebook](./examples/notebooks/quickstart.ipynb). More guides and tutorials will be added soon!
In the meanwhile, have a look at the other examples in the [examples](./examples/) directory.

## Usage examples & Docs
<img src="./.assets/docs.png" alt="open source docs bad" width="350"/>

While we do our best to provide excellent documentation, we are aware that it is not perfect. If you see anything missing or anything that could be improved, please don't hesitate to open an issue or a pull request.

### Examples
All examples can be found in the [examples](./examples/) directory. We do our best to thoroughly document each example, but if something is unclear, please don't hesitate to open an issue or a pull request in order to improve the documentation.

### Docs
The documentation can be found in the [docs](./docs/) directory. Here you will find both API documentation and some general guides such as [How to create a new tool](./docs/guides/creating_a_new_tool.md).

## Instructor & Model Compatibility
Atomic Agents depends on the [Instructor](https://github.com/jxnl/instructor) package. This means that in all examples where OpenAI is used, any other API supported by Instructor can be used, such as Cohere, Anthropic, Gemini, and more. For a complete list please refer to the instructor documentation on its [GitHub page](https://github.com/jxnl/instructor).

Additionally, Atomic Agents should work with Ollama or LMStudio. If the default settings do not work due to your local server not supporting tool-calling, you can set the `mode` to JSON.

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
