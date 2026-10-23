import pytest
from pydantic import ConfigDict

from atomic_agents.base import BaseIOSchema, BaseResource, BaseResourceConfig


class ReadInputSchema(BaseIOSchema):
    """Value requested from a resource."""

    model_config = ConfigDict(title="Read value")
    value: str


class ReadOutputSchema(BaseIOSchema):
    """Value returned by a resource."""

    value: str


class InheritedEchoResource(BaseResource[ReadInputSchema, ReadOutputSchema]):
    def read(self, input_data: ReadInputSchema) -> ReadOutputSchema:
        return ReadOutputSchema(value=input_data.value)


class ParameterizedEchoResource[InputSchema: BaseIOSchema, OutputSchema: BaseIOSchema](BaseResource):
    def read(self, input_data: InputSchema) -> OutputSchema:
        return self.output_schema.model_validate(input_data.model_dump())


def test_inherited_resource_schema_identity() -> None:
    resource = InheritedEchoResource()

    assert resource.input_schema is ReadInputSchema
    assert resource.output_schema is ReadOutputSchema


def test_parameterized_resource_schema_identity() -> None:
    resource = ParameterizedEchoResource[ReadInputSchema, ReadOutputSchema]()

    assert resource.input_schema is ReadInputSchema
    assert resource.output_schema is ReadOutputSchema


def test_untyped_resource_schema_defaults() -> None:
    resource = ParameterizedEchoResource()

    assert resource.input_schema is BaseIOSchema
    assert resource.output_schema is BaseIOSchema


def test_untyped_resource_metadata_defaults() -> None:
    resource = ParameterizedEchoResource()

    assert resource.resource_name == "BaseIOSchema"
    assert resource.resource_description == "Base schema for input/output in the Atomic Agents framework."


def test_resource_metadata_comes_from_input_schema() -> None:
    resource = InheritedEchoResource()

    assert resource.resource_name == "Read value"
    assert resource.resource_description == "Value requested from a resource."


def test_resource_title_override_preserves_schema_description() -> None:
    resource = InheritedEchoResource(config=BaseResourceConfig(title="Echo resource"))

    assert resource.resource_name == "Echo resource"
    assert resource.resource_description == "Value requested from a resource."


def test_resource_description_override_preserves_schema_title() -> None:
    resource = InheritedEchoResource(config=BaseResourceConfig(description="Configured description"))

    assert resource.resource_name == "Read value"
    assert resource.resource_description == "Configured description"


def test_resource_metadata_can_override_both_schema_values() -> None:
    resource = InheritedEchoResource(config=BaseResourceConfig(title="Echo resource", description="Configured description"))

    assert resource.resource_name == "Echo resource"
    assert resource.resource_description == "Configured description"


def test_empty_resource_metadata_falls_back_to_input_schema() -> None:
    resource = InheritedEchoResource(config=BaseResourceConfig(title="", description=""))

    assert resource.resource_name == "Read value"
    assert resource.resource_description == "Value requested from a resource."


@pytest.mark.parametrize("resource", [InheritedEchoResource(), ParameterizedEchoResource[ReadInputSchema, ReadOutputSchema]()])
def test_concrete_resource_read_returns_typed_value(resource: BaseResource[ReadInputSchema, ReadOutputSchema]) -> None:
    result = resource.read(ReadInputSchema(value="requested value"))

    assert type(result) is ReadOutputSchema
    assert result.value == "requested value"


def test_untyped_resource_read_returns_base_schema() -> None:
    result = ParameterizedEchoResource().read(BaseIOSchema())

    assert type(result) is BaseIOSchema
    assert result.model_dump() == {}
