# Atomic Agents Import Strategy Upgrade Guide

## Overview

Atomic Agents now provides **simplified import paths** that eliminate the need for the `.lib` directory in imports while maintaining full backward compatibility.

## What Changed

We've added module re-exports to the main package, allowing shorter, cleaner import paths:

- **Core classes**: All essential base classes available from main package
- **Module re-exports**: Components, factories, and utils accessible without `.lib`
- **Backward compatibility**: All existing import paths continue to work

## New Import Patterns

### Core Imports (Essential Classes)
All base classes available from the main package:
```python
from atomic_agents import BaseAgent, BaseAgentConfig, BaseIOSchema, BaseTool, BaseToolConfig
```

### Component Imports (Cleaner Paths)
**New (Recommended):**
```python
from atomic_agents.components import ChatHistory, SystemPromptGenerator
from atomic_agents.factories import fetch_mcp_tools_async, MCPTransportType
from atomic_agents.utils import format_tool_message
```

**Old (Still Works):**
```python
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools_async
from atomic_agents.lib.utils.format_tool_message import format_tool_message
```

## Migration Examples

### Basic Agent Creation
**Before:**
```python
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory
```

**After:**
```python
from atomic_agents import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.components import SystemPromptGenerator, ChatHistory
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
```

**After:**
```python
from atomic_agents.factories import fetch_mcp_tools_async, MCPTransportType
```

## Benefits

1. **Shorter imports**: Eliminated `.lib` from import paths
2. **Consistent API**: All base classes from main package
3. **Cleaner code**: More readable import statements
4. **Full compatibility**: No breaking changes

## Migration Strategy

### No Breaking Changes
All existing imports continue to work unchanged. The new patterns are optional improvements.

### Recommended Approach
1. **New projects**: Use the shorter import patterns
2. **Existing projects**: Update imports gradually or keep existing ones
3. **Mixed usage**: Both old and new patterns work together

## Important Notes

- **100% backward compatible**: All existing code works unchanged
- **Optional migration**: Update at your own pace
- **Choose your style**: Use whatever import style works best for your project

## Version Information

These import improvements are available starting from Atomic Agents v2.0.0.
