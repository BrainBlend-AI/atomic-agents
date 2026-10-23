from pydantic import ConfigDict

from atomic_agents.base import BaseIOSchema, BasePrompt, BasePromptConfig


class GreetingInput(BaseIOSchema):
    """Name of the person who will receive the greeting."""

    model_config = ConfigDict(title="Greeting request")

    name: str


class GreetingOutput(BaseIOSchema):
    """Greeting addressed to the requested person."""

    greeting: str


class GreetingPrompt(BasePrompt[GreetingInput, GreetingOutput]):
    def generate(self, params: GreetingInput) -> GreetingOutput:
        return GreetingOutput(greeting=f"Hello, {params.name}!")


class InheritedGreetingPrompt(GreetingPrompt):
    pass


class EmptyPrompt[InputSchema: BaseIOSchema, OutputSchema: BaseIOSchema](BasePrompt):
    def generate(self, params: InputSchema) -> OutputSchema:
        return self.output_schema()


def test_base_prompt_inherited_schema_identity():
    prompt = GreetingPrompt()

    assert prompt.input_schema is GreetingInput
    assert prompt.output_schema is GreetingOutput


def test_base_prompt_descendant_preserves_schema_identity():
    prompt = InheritedGreetingPrompt()

    assert prompt.input_schema is GreetingInput
    assert prompt.output_schema is GreetingOutput


def test_base_prompt_explicit_type_parameters_resolve_schema_identity():
    prompt = EmptyPrompt[GreetingInput, GreetingOutput]()

    assert prompt.input_schema is GreetingInput
    assert prompt.output_schema is GreetingOutput


def test_base_prompt_without_type_parameters_defaults_to_base_schema():
    prompt = EmptyPrompt()

    assert prompt.input_schema is BaseIOSchema
    assert prompt.output_schema is BaseIOSchema


def test_base_prompt_without_type_parameters_uses_base_schema_metadata():
    prompt = EmptyPrompt()

    assert prompt.prompt_name == "BaseIOSchema"
    assert prompt.prompt_description == "Base schema for input/output in the Atomic Agents framework."


def test_base_prompt_metadata_comes_from_input_schema():
    prompt = GreetingPrompt()

    assert prompt.prompt_name == "Greeting request"
    assert prompt.prompt_description == "Name of the person who will receive the greeting."


def test_base_prompt_explicit_type_parameters_use_input_schema_metadata():
    prompt = EmptyPrompt[GreetingInput, GreetingOutput]()

    assert prompt.prompt_name == "Greeting request"
    assert prompt.prompt_description == "Name of the person who will receive the greeting."


def test_base_prompt_config_overrides_both_metadata_fields():
    config = BasePromptConfig(title="Welcome", description="Welcome a new member.")
    prompt = GreetingPrompt(config=config)

    assert prompt.config is config
    assert prompt.prompt_name == "Welcome"
    assert prompt.prompt_description == "Welcome a new member."


def test_base_prompt_title_override_preserves_schema_description():
    prompt = GreetingPrompt(config=BasePromptConfig(title="Welcome"))

    assert prompt.prompt_name == "Welcome"
    assert prompt.prompt_description == "Name of the person who will receive the greeting."


def test_base_prompt_description_override_preserves_schema_title():
    prompt = GreetingPrompt(config=BasePromptConfig(description="Welcome a new member."))

    assert prompt.prompt_name == "Greeting request"
    assert prompt.prompt_description == "Welcome a new member."


def test_base_prompt_empty_metadata_overrides_use_schema_defaults():
    prompt = GreetingPrompt(config=BasePromptConfig(title="", description=""))

    assert prompt.prompt_name == "Greeting request"
    assert prompt.prompt_description == "Name of the person who will receive the greeting."


def test_greeting_prompt_generate_returns_greeting_schema_and_value():
    prompt = GreetingPrompt()

    result = prompt.generate(GreetingInput(name="Ada"))

    assert type(result) is GreetingOutput
    assert result.greeting == "Hello, Ada!"


def test_untyped_prompt_generate_returns_empty_base_schema():
    prompt = EmptyPrompt()

    result = prompt.generate(BaseIOSchema())

    assert type(result) is BaseIOSchema
    assert result.model_dump() == {}
