---
name: find-forge-tools
description: Find and download an existing Atomic Forge tool before writing one from scratch. Use when an Atomic Agents project needs a tool capability, such as search, scraping, weather, PDF, or date/time support.
---

# Find Forge Tools

Check Atomic Forge before creating a tool from scratch. A Forge is a Git repository with an index of downloadable tools, so configured sources can include private forges through the user's existing Git credentials.

## 1. Search the configured forges

From the project root, run:

```bash
atomic list
```

This searches every configured source. If the CLI is unavailable, read `atomic-forge/index.json` in the repository instead. Match the requested capability against the tool name and description. If names overlap, keep the `source/name` form shown by `atomic list`.

## 2. Download a match

Download the matching tool into the project:

```bash
atomic download <name>
```

Use the source-qualified name when needed:

```bash
atomic download <source>/<name>
```

If the project needs a specific destination, pass the supported destination flag:

```bash
atomic download <name> --dest <directory>
```

Read the downloaded README and wire the tool into the agent's tool list. Confirm its dependencies and configuration before running it.

## 3. Hand off when there is no match

When the forge index has no suitable tool, continue with the `create-atomic-tool` skill at `../create-atomic-tool/SKILL.md`. It covers the schemas, `BaseTool` implementation, configuration, failure outputs, and verification for a new in-project tool.

If a new tool would be useful to other projects, package it for the Forge format after implementing it and add it to the relevant source index.
