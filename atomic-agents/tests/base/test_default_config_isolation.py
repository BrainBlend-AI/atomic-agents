import pytest

from atomic_agents.base import BaseIOSchema, BasePrompt, BaseResource, BaseTool


class ValueSchema(BaseIOSchema):
    """A value passed through a component."""

    value: str


class EchoTool(BaseTool[ValueSchema, ValueSchema]):
    def run(self, params: ValueSchema) -> ValueSchema:
        return params


class EchoResource(BaseResource[ValueSchema, ValueSchema]):
    def read(self, params: ValueSchema) -> ValueSchema:
        return params


class EchoPrompt(BasePrompt[ValueSchema, ValueSchema]):
    def generate(self, params: ValueSchema) -> ValueSchema:
        return params


@pytest.mark.parametrize(
    "component_class, name_attribute, description_attribute",
    [
        (EchoTool, "tool_name", "tool_description"),
        (EchoResource, "resource_name", "resource_description"),
        (EchoPrompt, "prompt_name", "prompt_description"),
    ],
)
def test_default_config_changes_do_not_affect_other_instances(
    component_class: type[EchoTool] | type[EchoResource] | type[EchoPrompt],
    name_attribute: str,
    description_attribute: str,
) -> None:
    first = component_class()
    second = component_class()
    original_title, original_description = first.config.title, first.config.description

    try:
        first.config.title = "Customized instance"
        first.config.description = "Only this instance should change."

        assert getattr(first, name_attribute) == "Customized instance"
        assert getattr(first, description_attribute) == "Only this instance should change."
        for other in (second, component_class()):
            assert getattr(other, name_attribute) == "ValueSchema"
            assert getattr(other, description_attribute) == ValueSchema.__doc__
    finally:
        first.config.title, first.config.description = original_title, original_description


@pytest.mark.parametrize("component_class", [EchoTool, EchoResource, EchoPrompt])
def test_explicit_config_is_retained(component_class: type[EchoTool] | type[EchoResource] | type[EchoPrompt]) -> None:
    config = component_class().config
    component = component_class(config=config)

    assert component.config is config
