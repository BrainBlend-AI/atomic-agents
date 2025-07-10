# Atomic Agents Import Simplification Upgrade Guide

## Overview

We have significantly improved the import system for Atomic Agents by adding strategic `__init__.py` files throughout the codebase. This allows for much shorter, cleaner imports while maintaining full backward compatibility.

## What Changed

### New `__init__.py` Files Added

1. **Main Package**: `/atomic_agents/__init__.py`
2. **Library Module**: `/atomic_agents/lib/__init__.py`
3. **Agents Module**: `/atomic_agents/agents/__init__.py` (enhanced)
4. **Components Module**: `/atomic_agents/lib/components/__init__.py` (enhanced)
5. **Base Module**: `/atomic_agents/lib/base/__init__.py`
6. **Utils Module**: `/atomic_agents/lib/utils/__init__.py` (enhanced)
7. **Factories Module**: `/atomic_agents/lib/factories/__init__.py`

### Core Exports Available

The main `atomic_agents` package now exports these key classes directly:

- `BaseAgent`, `BaseAgentConfig`, `BaseAgentInputSchema`, `BaseAgentOutputSchema`
- `BaseIOSchema`
- `BaseTool`, `BaseToolConfig`
- `ChatHistory`
- `SystemPromptGenerator`, `SystemPromptContextProviderBase`

## New Import Options

### 1. Top-Level Imports (Shortest)

**Before:**
```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory
```

**After:**
```python
from atomic_agents import (
    BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseIOSchema,
    SystemPromptGenerator, ChatHistory
)
```

### 2. Module-Level Imports (Organized)

**Before:**
```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory
```

**After:**
```python
from atomic_agents.agents import BaseAgent, BaseAgentConfig
from atomic_agents.lib import BaseIOSchema, SystemPromptGenerator, ChatHistory
```

### 3. Namespace Imports (Clean)

**Before:**
```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
```

**After:**
```python
import atomic_agents as aa

agent = aa.BaseAgent[aa.BaseAgentInputSchema, aa.BaseAgentOutputSchema](
    config=aa.BaseAgentConfig(...)
)
```

### 4. Specific Module Imports

**Tools:**
```python
# Before
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig

# After
from atomic_agents.lib.base import BaseTool, BaseToolConfig
# OR
from atomic_agents import BaseTool, BaseToolConfig
```

**Components:**
```python
# Before
from atomic_agents.lib.components.chat_history import ChatHistory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# After
from atomic_agents.lib.components import ChatHistory, SystemPromptGenerator
# OR
from atomic_agents import ChatHistory, SystemPromptGenerator
```

**Utilities:**
```python
# Before
from atomic_agents.lib.utils.format_tool_message import format_tool_message

# After
from atomic_agents.lib.utils import format_tool_message
# OR
from atomic_agents.lib import format_tool_message
```

## Updated Examples

### Basic Chatbot Example

**Before:**
```python
import instructor
import openai
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from atomic_agents.lib.components.chat_history import ChatHistory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
```

**After (Option 1 - Top-level):**
```python
import instructor
import openai
from atomic_agents import (
    BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema,
    ChatHistory, SystemPromptGenerator
)
```

**After (Option 2 - Module-level):**
```python
import instructor
import openai
from atomic_agents.agents import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from atomic_agents.lib import ChatHistory, SystemPromptGenerator
```

### Custom Tool Example

**Before:**
```python
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
```

**After:**
```python
from atomic_agents import BaseTool, BaseToolConfig, BaseIOSchema
```

### Custom Schema Example

**Before:**
```python
from pydantic import Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
```

**After:**
```python
from pydantic import Field
from atomic_agents import BaseIOSchema, BaseAgent, BaseAgentConfig, BaseAgentInputSchema
```

## Basic PDF Analysis Example - Generic Type Parameters

### Issue Fixed
The `basic-pdf-analysis` example was missing generic type parameters in the BaseAgent declaration, causing it to return `BaseAgentOutputSchema` instead of the custom `ExtractionResult` schema.

### Change Made
**Before:**
```python
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gemini-2.0-flash",
        system_prompt_generator=system_prompt_generator,
        input_schema=InputSchema,
        output_schema=ExtractionResult,
    )
)
```

**After:**
```python
agent = BaseAgent[InputSchema, ExtractionResult](
    config=BaseAgentConfig(
        client=client,
        model="gemini-2.0-flash",
        system_prompt_generator=system_prompt_generator,
        input_schema=InputSchema,
        output_schema=ExtractionResult,
    )
)
```

### Why This Fix Was Needed
Without the generic type parameters `[InputSchema, ExtractionResult]`, the BaseAgent falls back to the default `BaseAgentOutputSchema`, causing attribute errors when trying to access custom schema fields like `pdf_title`, `page_count`, and `summary`.

## Benefits

1. **Reduced Import Depth**: From 4 levels deep to 1-2 levels
2. **Cleaner Code**: Less verbose import statements
3. **Better Developer Experience**: Easier to remember and type imports
4. **Backward Compatible**: All existing imports continue to work
5. **Flexible**: Multiple import styles supported based on preference
6. **IDE Friendly**: Better autocomplete with flatter import structure

## Migration Strategy

### Immediate Benefits (No Code Changes Required)
- All existing code continues to work unchanged
- No breaking changes introduced

### Optional Migration (For Cleaner Code)
You can gradually update your imports to use the shorter forms:

1. **Start with new projects**: Use the new short imports for new code
2. **Gradual updates**: Update existing files when you're already modifying them
3. **Bulk updates**: Use find/replace to update all imports at once (optional)

### Recommended Approach

For **new projects**, we recommend:
```python
# Primary imports - most common classes
from atomic_agents import BaseAgent, BaseAgentConfig, BaseIOSchema, ChatHistory

# Specific imports as needed
from atomic_agents.lib.components import SystemPromptGenerator
```

For **existing projects**, you can:
1. Keep current imports (they all still work)
2. Gradually adopt shorter imports when convenient
3. Use mixed approaches as needed

## No Breaking Changes

**Important**: This upgrade is 100% backward compatible. All existing import statements will continue to work exactly as before. The new shorter imports are additional options, not replacements.

## Version Information

These import improvements are available starting from Atomic Agents v2.0.0.

## Examples in the Wild

Check the updated examples in the repository to see the new import patterns in action:
- `/atomic-examples/quickstart/`
- `/atomic-examples/web-search-agent/`
- `/atomic-examples/rag-chatbot/`

The examples demonstrate both old and new import styles to help with your migration.
