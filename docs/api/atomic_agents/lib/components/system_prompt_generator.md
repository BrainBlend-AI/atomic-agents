# SystemPromptGenerator

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Components](./index.md#components) / SystemPromptGenerator

> Auto-generated documentation for [atomic_agents.lib.components.system_prompt_generator](../../../../../atomic_agents/lib/components/system_prompt_generator.py) module.

- [SystemPromptGenerator](#systempromptgenerator)
  - [CurrentDateProvider](#currentdateprovider)
    - [CurrentDateProvider().get_info](#currentdateprovider()get_info)
  - [LoremIpsumProvider](#loremipsumprovider)
    - [LoremIpsumProvider().get_info](#loremipsumprovider()get_info)
  - [SystemPromptContextProviderBase](#systempromptcontextproviderbase)
    - [SystemPromptContextProviderBase().get_info](#systempromptcontextproviderbase()get_info)
  - [SystemPromptGenerator](#systempromptgenerator-1)
    - [SystemPromptGenerator().generate_prompt](#systempromptgenerator()generate_prompt)
  - [SystemPromptInfo](#systempromptinfo)

## CurrentDateProvider

[Show source in system_prompt_generator.py:56](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L56)

#### Signature

```python
class CurrentDateProvider(SystemPromptContextProviderBase):
    def __init__(self, format: str = "%Y-%m-%d %H:%M:%S", **kwargs): ...
```

#### See also

- [SystemPromptContextProviderBase](#systempromptcontextproviderbase)

### CurrentDateProvider().get_info

[Show source in system_prompt_generator.py:61](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L61)

#### Signature

```python
def get_info(self) -> str: ...
```



## LoremIpsumProvider

[Show source in system_prompt_generator.py:64](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L64)

#### Signature

```python
class LoremIpsumProvider(SystemPromptContextProviderBase): ...
```

#### See also

- [SystemPromptContextProviderBase](#systempromptcontextproviderbase)

### LoremIpsumProvider().get_info

[Show source in system_prompt_generator.py:65](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L65)

#### Signature

```python
def get_info(self) -> str: ...
```



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

[Show source in system_prompt_generator.py:21](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L21)

#### Signature

```python
class SystemPromptGenerator:
    def __init__(self, system_prompt_info: SystemPromptInfo = None): ...
```

#### See also

- [SystemPromptInfo](#systempromptinfo)

### SystemPromptGenerator().generate_prompt

[Show source in system_prompt_generator.py:30](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L30)

#### Signature

```python
def generate_prompt(self) -> str: ...
```



## SystemPromptInfo

[Show source in system_prompt_generator.py:15](../../../../../atomic_agents/lib/components/system_prompt_generator.py#L15)

#### Signature

```python
class SystemPromptInfo: ...
```