# Atomic Forge
Atomic Forge is a collection of tools that can be used with Atomic Agents to extend its functionality and integrate with other services.

**Note:** Atomic Forge is NOT a package, but a folder of downloadable tools. This may seem strange at first, but it improves the developer experience in several ways:

1. **Full Control:** You have full ownership and control over each tool that you download. Do you like the Search tool, but wish it would sort results in a specific way? You can change it without impacting other users! Though if your change is useful for others, feel free to submit a pull request to the Atomic Forge repository.
2. **Dependency Management:** Because the tool resides in your own codebase once downloaded, you have better control over dependencies.
3. **Lightweight:** Because each tool is a standalone component, you can download only the tools that you need, rather than bloating your project with many unnecessary dependencies. After all, you don't need dependencies such as Sympy if you are not using the Calculator tool!

## Using the Atomic Assembler CLI
Please use the [Atomic Assembler CLI](../README.md) as mentioned in the main [README.md](/README.md) for managing and downloading Tools.

## Tools
The Atomic Forge project includes the following tools:

- [Calculator](/atomic-forge/tools/calculator/README.md)
- [SearXNG Search](/atomic-forge/tools/searxng_search/README.md)
- [Tavily Search](/atomic-forge/tools/tavily_search/README.md)
- [YouTube Transcript Scraper](/atomic-forge/tools/youtube_transcript_scraper/README.md)
- [Webpage Scraper](/atomic-forge/tools/webpage_scraper/README.md)

## Creating Custom Tools
Creating your own tools is easy! See the [Creating Tools](/atomic-forge/guides/tool_structure.md) guide for more information.
