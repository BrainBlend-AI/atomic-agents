# Atomic Agents Development Guide

This guide provides instructions for developers who want to contribute to the Atomic Agents project. It covers the project structure, setup, development workflow, and best practices.

## Project Structure

Atomic Agents uses a monorepo structure, which means multiple related projects are managed in a single repository. The main components are:

1. `atomic-agents/`: The core Atomic Agents library
2. `atomic-assembler/`: The CLI tool for managing Atomic Agents components
3. `atomic-examples/`: Example projects showcasing Atomic Agents usage
4. `atomic-forge/`: A collection of tools that can be used with Atomic Agents

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- Git

### Setting Up the Development Environment

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/BrainBlend-AI/atomic-agents.git
   cd atomic-agents
   ```
3. Install dependencies using Poetry:
   ```
   poetry install
   ```
4. Activate the virtual environment:
   ```
   poetry shell
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```
   git checkout -b feature-branch
   ```

2. Make your changes in the appropriate project directory.

3. Format your code using Black:
   ```
   black atomic_agents atomic_assembler
   ```

4. Lint your code using Flake8:
   ```
   flake8 atomic_agents atomic_assembler
   ```

5. Run the tests:
   ```
   pytest --cov atomic_agents
   ```

6. If you've added new functionality, make sure to add appropriate tests.

7. Commit your changes:
   ```
   git commit -m 'Add some feature'
   ```

8. Push to your fork:
   ```
   git push origin feature-branch
   ```

9. Open a pull request on GitHub.

## Code Style and Best Practices

- Follow PEP 8 guidelines for Python code style.
- Use type hints wherever possible.
- Write clear, concise docstrings for all public modules, functions, classes, and methods.
- Keep functions and methods small and focused on a single responsibility.
- Use meaningful variable and function names.

## Testing

- Write unit tests for all new functionality.
- Make sure to get 100% test coverage for all new functionality.
- Run the test suite before submitting a pull request:
  ```
  pytest --cov atomic_agents
  ```
- To view a detailed coverage report:
  ```
  coverage html
  ```
  This will generate an HTML report in the `htmlcov/` directory.

## Documentation

- Update the README.md file if you've added new features or changed existing functionality.
- If you've added new modules or significant features, consider updating the API documentation.

## Submitting Changes

- Create a pull request with a clear title and description.
- Link any relevant issues in the pull request description.
- Make sure all tests pass and there are no linting errors.
- Be responsive to code review feedback and make necessary changes.

## Questions and Support

If you have any questions or need support while developing, please open an issue on GitHub or reach out to the maintainers.

Thank you for contributing to Atomic Agents!
