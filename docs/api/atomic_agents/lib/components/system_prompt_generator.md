# SystemPromptGenerator

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Components](./index.md#components) / SystemPromptGenerator

> Auto-generated documentation for [atomic_agents.lib.components.system_prompt_generator](../../../../../atomic_agents/lib/components/system_prompt_generator.py) module.

- [SystemPromptGenerator](#systempromptgenerator)
  - [SystemPromptContextProviderBase](#systempromptcontextproviderbase)
    - [SystemPromptContextProviderBase().get_info](#systempromptcontextproviderbase()get_info)
  - [SystemPromptGenerator](#systempromptgenerator-1)
    - [SystemPromptGenerator().generate_prompt](#systempromptgenerator()generate_prompt)

## SystemPromptContextProviderBase

[Show source in system_prompt_generator.py:5](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L5)

#### Signature

```python
class SystemPromptContextProviderBase(ABC):
    def __init__(self, title: str): ...
```

### SystemPromptContextProviderBase().get_info

[Show source in system_prompt_generator.py:9](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L9)

#### Signature

```python
@abstractmethod
def get_info(self) -> str: ...
```



## SystemPromptGenerator

[Show source in system_prompt_generator.py:17](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L17)

#### Signature

```python
class SystemPromptGenerator:
    def __init__(
        self,
        background: Optional[List[str]] = None,
        steps: Optional[List[str]] = None,
        output_instructions: Optional[List[str]] = None,
        context_providers: Optional[Dict[str, SystemPromptContextProviderBase]] = None,
    ): ...
```

#### See also

- [SystemPromptContextProviderBase](#systempromptcontextproviderbase)

### SystemPromptGenerator().generate_prompt

[Show source in system_prompt_generator.py:37](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L37)

#### Signature

```python
def generate_prompt(self) -> str: ...
```