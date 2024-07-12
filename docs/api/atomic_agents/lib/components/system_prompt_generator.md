# SystemPromptGenerator

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Components](./index.md#components) / SystemPromptGenerator

> Auto-generated documentation for [atomic_agents.lib.components.system_prompt_generator](../../../../../atomic_agents/lib/components/system_prompt_generator.py) module.

- [SystemPromptGenerator](#systempromptgenerator)
  - [SystemPromptContextProviderBase](#systempromptcontextproviderbase)
    - [SystemPromptContextProviderBase().get_info](#systempromptcontextproviderbase()get_info)
  - [SystemPromptGenerator](#systempromptgenerator-1)
    - [SystemPromptGenerator().generate_prompt](#systempromptgenerator()generate_prompt)
  - [SystemPromptInfo](#systempromptinfo)

## SystemPromptContextProviderBase

[Show source in system_prompt_generator.py:6](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L6)

#### Signature

```python
class SystemPromptContextProviderBase(ABC):
    def __init__(self, title: str): ...
```

### SystemPromptContextProviderBase().get_info

[Show source in system_prompt_generator.py:10](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L10)

#### Signature

```python
@abstractmethod
def get_info(self) -> str: ...
```



## SystemPromptGenerator

[Show source in system_prompt_generator.py:26](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L26)

#### Signature

```python
class SystemPromptGenerator:
    def __init__(self, system_prompt_info: Optional[SystemPromptInfo] = None): ...
```

#### See also

- [SystemPromptInfo](#systempromptinfo)

### SystemPromptGenerator().generate_prompt

[Show source in system_prompt_generator.py:39](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L39)

#### Signature

```python
def generate_prompt(self) -> str: ...
```



## SystemPromptInfo

[Show source in system_prompt_generator.py:19](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L19)

#### Signature

```python
class SystemPromptInfo: ...
```