# SystemPromptGenerator

[Atomic_agents_redux Index](../../../README.md#atomic_agents_redux-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Components](./index.md#components) / SystemPromptGenerator

> Auto-generated documentation for [atomic_agents.lib.components.system_prompt_generator](../../../../atomic_agents/lib/components/system_prompt_generator.py) module.

- [SystemPromptGenerator](#systempromptgenerator)
  - [DynamicInfoProviderBase](#dynamicinfoproviderbase)
    - [DynamicInfoProviderBase().get_info](#dynamicinfoproviderbase()get_info)
  - [SystemPromptGenerator](#systempromptgenerator-1)
    - [SystemPromptGenerator().generate_prompt](#systempromptgenerator()generate_prompt)
  - [SystemPromptInfo](#systempromptinfo)

## DynamicInfoProviderBase

[Show source in system_prompt_generator.py:10](../../../../atomic_agents/lib/components/system_prompt_generator.py#L10)

#### Signature

```python
class DynamicInfoProviderBase(ABC):
    def __init__(self, title: str): ...
```

### DynamicInfoProviderBase().get_info

[Show source in system_prompt_generator.py:14](../../../../atomic_agents/lib/components/system_prompt_generator.py#L14)

#### Signature

```python
@abstractmethod
def get_info(self) -> str: ...
```



## SystemPromptGenerator

[Show source in system_prompt_generator.py:18](../../../../atomic_agents/lib/components/system_prompt_generator.py#L18)

#### Signature

```python
class SystemPromptGenerator:
    def __init__(
        self,
        system_prompt_info: SystemPromptInfo = None,
        dynamic_info_providers: dict[str, DynamicInfoProviderBase] = None,
    ): ...
```

#### See also

- [DynamicInfoProviderBase](#dynamicinfoproviderbase)
- [SystemPromptInfo](#systempromptinfo)

### SystemPromptGenerator().generate_prompt

[Show source in system_prompt_generator.py:27](../../../../atomic_agents/lib/components/system_prompt_generator.py#L27)

#### Signature

```python
def generate_prompt(self) -> str: ...
```



## SystemPromptInfo

[Show source in system_prompt_generator.py:5](../../../../atomic_agents/lib/components/system_prompt_generator.py#L5)

#### Signature

```python
class SystemPromptInfo(BaseModel): ...
```