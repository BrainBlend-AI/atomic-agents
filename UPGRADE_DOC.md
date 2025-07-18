# Atomic Agents Import Strategy Upgrade Guide

## Overview

Atomic Agents now provides **simplified import paths** that eliminate the need for the `.lib` directory in imports. This is a breaking change that requires updating import paths.

## What Changed

We've refactored the package structure to use module re-exports, allowing shorter, cleaner import paths:

- **Core classes**: All essential base classes available from main package
- **Module re-exports**: Components moved to `context`, factories moved to `connectors` with MCP-specific functionality under `connectors.mcp`
- **Class renames**: `SystemPromptContextProviderBase` → `BaseDynamicContextProvider`
- **Breaking change**: Old import paths using `.lib` are no longer supported.

## New Import Patterns

### Core Imports (Essential Classes)
All base classes available from the main package:
```python
from atomic_agents import BaseAgent, BaseAgentConfig, BaseIOSchema, BaseTool, BaseToolConfig
```

### Context Imports (Cleaner Paths)
**New (Recommended):**
```python
from atomic_agents.context import ChatHistory, SystemPromptGenerator, BaseDynamicContextProvider
from atomic_agents.connectors.mcp import fetch_mcp_tools_async, MCPTransportType
from atomic_agents.utils import format_tool_message
```

**Old (No Longer Works):**
```python
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase
from atomic_agents.lib.components.chat_history import ChatHistory
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools_async
from atomic_agents.lib.factories.tool_definition_service import MCPTransportType
from atomic_agents.lib.utils.format_tool_message import format_tool_message
```

## Migration Examples

### Basic Agent Creation
**Before:**
```python
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase
from atomic_agents.lib.components.chat_history import ChatHistory
```

**After:**
```python
from atomic_agents import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.context import SystemPromptGenerator, BaseDynamicContextProvider, ChatHistory
```

### Custom Tool Creation
**Before:**
```python
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
```

**After:**
```python
from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig
```

### MCP Integration
**Before:**
```python
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools_async
from atomic_agents.lib.factories.tool_definition_service import MCPTransportType
```

**After:**
```python
from atomic_agents.connectors.mcp import fetch_mcp_tools_async, MCPTransportType
```

## Benefits

1. **Shorter imports**: Eliminated `.lib` from import paths
2. **Consistent API**: All base classes from main package
3. **Cleaner code**: More readable import statements
4. **Better organization**: 
   - `components` → `context` (better reflects purpose)
   - `factories` → `connectors` with MCP-specific functionality grouped under `connectors.mcp`
   - `connectors` structure allows future extension for agent-to-agent communications and other connectivity modules
   - More intuitive class naming (`BaseDynamicContextProvider` vs `SystemPromptContextProviderBase`)

## Migration Strategy

### Required Migration
This upgrade introduces breaking changes. All projects must be updated to use the new import paths.

### Recommended Approach
1. **Update all imports**: Replace old `.lib` imports with the new, shorter paths.
2. **Test thoroughly**: Ensure all parts of your application work as expected after the migration.

## Important Notes

- **Breaking Changes**: This version is not backward compatible.
- **Mandatory Migration**: You must update your import paths to continue using the library.

## Version Information

These import improvements are available starting from Atomic Agents v2.0.0.
