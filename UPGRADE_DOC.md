# Atomic Agents Import Strategy Upgrade Guide

## Overview

Atomic Agents now uses a **tiered import strategy** that organizes imports by usage frequency and logical grouping, rather than pulling everything to the top level. This provides cleaner namespaces while maintaining full backward compatibility.

## What Changed

We've moved from a "pull everything to the top" approach to a structured tiered system:

- **Core tier**: Essential classes (90% of users)
- **Common tier**: Frequently used components  
- **Specialized tier**: Advanced functionality

## New Import Patterns

### Core Imports (90% of users)
Essential classes for basic agent creation:
```python
from atomic_agents import BaseAgent, BaseAgentConfig, BaseIOSchema
```

### Common Imports (building full applications)
Components and utilities for complete applications:
```python
from atomic_agents.lib import ChatHistory, SystemPromptGenerator, BaseTool
from atomic_agents.agents import BaseAgentInputSchema, BaseAgentOutputSchema
```

### Specialized Imports (advanced features)
For specific functionality:
```python
from atomic_agents.lib.factories import MCPToolFactory, fetch_mcp_tools
from atomic_agents.lib.utils import format_tool_message
```

## Migration Examples

### Basic Agent Creation
**Before:**
```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory
```

**After:**
```python
from atomic_agents import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib import ChatHistory, SystemPromptGenerator
from atomic_agents.agents import BaseAgentInputSchema
```

### Custom Tool Creation
**Before:**
```python
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
```

**After:**
```python
from atomic_agents import BaseIOSchema
from atomic_agents.lib import BaseTool, BaseToolConfig
```

## Benefits

1. **Cleaner namespaces**: Top-level package only exports essentials
2. **Logical organization**: Import paths reflect component purpose
3. **Reduced maintenance**: Fewer cascading changes needed
4. **Better performance**: Smaller import footprint
5. **Clear intent**: Import structure indicates usage patterns

## Migration Strategy

### No Breaking Changes
All existing imports continue to work unchanged. The new patterns are optional improvements.

### Recommended Approach
1. **New projects**: Use the tiered import patterns
2. **Existing projects**: Gradually adopt new patterns when convenient
3. **Mixed usage**: Feel free to mix old and new patterns as needed

## Important Notes

- **100% backward compatible**: All existing code works unchanged
- **Optional migration**: Update at your own pace
- **Multiple styles supported**: Choose what works best for your project

## Version Information

These import improvements are available starting from Atomic Agents v2.0.0.
