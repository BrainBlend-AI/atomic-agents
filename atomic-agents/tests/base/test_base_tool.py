from pydantic import BaseModel
from atomic_agents import BaseToolConfig, BaseTool, BaseIOSchema


# Mock classes for testing
class MockInputSchema(BaseIOSchema):
    """Mock input schema for testing"""

    query: str


class MockOutputSchema(BaseIOSchema):
    """Mock output schema for testing"""

    result: str


class MockTool[InputSchema: BaseIOSchema, OutputSchema: BaseIOSchema](BaseTool):
    def run(self, params: InputSchema) -> OutputSchema:
        if self.output_schema == MockOutputSchema:
            return MockOutputSchema(result="Mock result")
        elif self.output_schema == BaseIOSchema:
            return BaseIOSchema()
        else:
            raise ValueError("Unsupported output schema")


def test_base_tool_config_creation():
    config = BaseToolConfig()
    assert config.title is None
    assert config.description is None


def test_base_tool_config_with_values():
    config = BaseToolConfig(title="Test Tool", description="Test description")
    assert config.title == "Test Tool"
    assert config.description == "Test description"


def test_base_tool_initialization_without_type_parameters():
    tool = MockTool()
    assert tool.tool_name == "BaseIOSchema"
    assert tool.tool_description == "Base schema for input/output in the Atomic Agents framework."
    assert tool.output_schema == BaseIOSchema


def test_base_tool_initialization():
    tool = MockTool[MockInputSchema, MockOutputSchema]()
    assert tool.tool_name == "MockInputSchema"
    assert tool.tool_description == "Mock input schema for testing"


def test_base_tool_with_config():
    config = BaseToolConfig(title="Custom Title", description="Custom description")
    tool = MockTool[MockInputSchema, MockOutputSchema](config=config)
    assert tool.tool_name == "Custom Title"
    assert tool.tool_description == "Custom description"


def test_base_tool_with_custom_title():
    config = BaseToolConfig(title="Custom Tool Name")
    tool = MockTool[MockInputSchema, MockOutputSchema](config=config)
    assert tool.tool_name == "Custom Tool Name"
    assert tool.tool_description == "Mock input schema for testing"


def test_mock_tool_run():
    tool = MockTool[MockInputSchema, MockOutputSchema]()
    result = tool.run(MockInputSchema(query="mock query"))
    assert isinstance(result, MockOutputSchema)
    assert result.result == "Mock result"


def test_base_tool_input_schema():
    tool = MockTool[MockInputSchema, MockOutputSchema]()
    assert tool.input_schema == MockInputSchema


def test_base_tool_output_schema():
    tool = MockTool[MockInputSchema, MockOutputSchema]()
    assert tool.output_schema == MockOutputSchema


def test_base_tool_inheritance():
    tool = MockTool[MockInputSchema, MockOutputSchema]()
    assert isinstance(tool, BaseTool)


def test_base_tool_config_is_pydantic_model():
    assert issubclass(BaseToolConfig, BaseModel)


def test_base_tool_config_optional_fields():
    config = BaseToolConfig()
    assert hasattr(config, "title")
    assert hasattr(config, "description")


# Test for GitHub issue #161 fix: proper schema resolution
def test_base_tool_schema_resolution():
    """Test that input_schema and output_schema return correct types (not BaseIOSchema)"""

    class CustomInput(BaseIOSchema):
        """Custom input schema for testing"""

        name: str

    class CustomOutput(BaseIOSchema):
        """Custom output schema for testing"""

        result: str

    class TestTool(BaseTool[CustomInput, CustomOutput]):
        def run(self, params: CustomInput) -> CustomOutput:
            return CustomOutput(result=f"processed_{params.name}")

    tool = TestTool()

    # These should return the specific types, not BaseIOSchema
    assert tool.input_schema == CustomInput
    assert tool.output_schema == CustomOutput
    assert tool.input_schema != BaseIOSchema
    assert tool.output_schema != BaseIOSchema
