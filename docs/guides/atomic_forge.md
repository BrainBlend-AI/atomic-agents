# Atomic Forge and Assembler

The **Atomic Forge** is a collection of standalone tool packages. You download a tool into your project, review the source, and own the copy. Tools become part of your codebase, so you can change them for your use case and install only the dependencies you need.

The **Atomic Assembler** is the `atomic` CLI for browsing and downloading Forge tools.

## Quick workflow

List the tools in your configured Forge sources:

```bash
atomic list
```

Download a tool by name:

```bash
atomic download <name>
```

If two sources contain the same tool, use `source/name` as the name. Choose a destination with `--dest`:

```bash
atomic download <name> --dest ./tools/<name>
```

The downloaded package includes its source, tests, `pyproject.toml`, and `requirements.txt`. Install its runtime dependencies, then use the tool as Python code in your project:

```bash
pip install -r ./<name>/requirements.txt
```

See the downloaded tool's `README.md` for its import and usage example. `atomic download --help` shows the current command options.

## Private and additional Forges

A Forge is any Git repository with a `tools/` directory and an `index.json` file. To make your own Forge, add tool packages under `tools/`, then generate the index from the repository root:

```bash
python atomic-forge/scripts/generate_index.py
```

The generator reads each tool's `pyproject.toml` and writes the Forge `index.json`. Commit both the tools and the generated index. A private Forge uses the same layout and does not need a registry service.

Add it to your local source list with a name and Git URL:

```bash
atomic sources add company https://git.example.com/company/atomic-forge.git
```

For a non-default branch or tools directory, pass the shipped options:

```bash
atomic sources add company https://git.example.com/company/atomic-forge.git \
  --branch main --tools-path tools
```

The Assembler clones sources with your normal Git setup. Configure authentication through Git credentials, SSH keys, or your usual credential helper. The Forge does not handle credentials itself.

Use these commands to inspect or remove configured sources:

```bash
atomic sources list
atomic sources remove company
```

Run `atomic sources add --help` for all available flags.

## Forge tool conformance

Every Forge tool follows the same package contract:

- It has one focused responsibility and can run independently.
- Its input and output schemas inherit from `BaseIOSchema`.
- Its configuration inherits from `BaseToolConfig`.
- Its main tool class inherits from `BaseTool`.
- It keeps implementation code in `tool/` and tests in `tests/`.
- It includes `pyproject.toml`, `README.md`, and a runtime-only `requirements.txt`.
- Its README documents purpose, configuration, and usage.

The complete standard, including the expected package layout and authoring details, is in the [Atomic Tool structure guide](https://github.com/eigenwise/atomic-agents/blob/main/atomic-forge/guides/tool_structure.md).

When you want an assisted authoring workflow, use the `create-atomic-tool` skill from the Atomic Agents Claude plugin. It walks through the schemas, configuration, implementation, tests, verification, and hand-off for a distributable tool.

## Related guides

- [Tools Guide](tools.md): compose tools with agents and application code.
- [Atomic Forge directory](https://github.com/eigenwise/atomic-agents/tree/main/atomic-forge): browse the shipped tools and Forge files.
