from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase


class MockContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str, info: str):
        super().__init__(title)
        self._info = info

    def get_info(self) -> str:
        return self._info


def test_system_prompt_generator_default_initialization():
    generator = SystemPromptGenerator()
    assert generator.background == ["This is a conversation with a helpful and friendly AI assistant."]
    assert generator.steps == []
    assert generator.output_instructions == [
        "Always respond using the proper JSON schema.",
        "Always use the available additional information and context to enhance the response.",
    ]
    assert generator.context_providers == {}


def test_system_prompt_generator_custom_initialization():
    background = ["Custom background"]
    steps = ["Step 1", "Step 2"]
    output_instructions = ["Custom instruction"]
    context_providers = {
        "provider1": MockContextProvider("Provider 1", "Info 1"),
        "provider2": MockContextProvider("Provider 2", "Info 2"),
    }

    generator = SystemPromptGenerator(
        background=background, steps=steps, output_instructions=output_instructions, context_providers=context_providers
    )

    assert generator.background == background
    assert generator.steps == steps
    assert generator.output_instructions == [
        "Custom instruction",
        "Always respond using the proper JSON schema.",
        "Always use the available additional information and context to enhance the response.",
    ]
    assert generator.context_providers == context_providers


def test_generate_prompt_without_context_providers():
    generator = SystemPromptGenerator(
        background=["Background info"], steps=["Step 1", "Step 2"], output_instructions=["Custom instruction"]
    )

    expected_prompt = """# IDENTITY and PURPOSE
- Background info

# INTERNAL ASSISTANT STEPS
- Step 1
- Step 2

# OUTPUT INSTRUCTIONS
- Custom instruction
- Always respond using the proper JSON schema.
- Always use the available additional information and context to enhance the response."""

    assert generator.generate_prompt() == expected_prompt


def test_generate_prompt_with_context_providers():
    generator = SystemPromptGenerator(
        background=["Background info"],
        steps=["Step 1"],
        output_instructions=["Custom instruction"],
        context_providers={
            "provider1": MockContextProvider("Provider 1", "Info 1"),
            "provider2": MockContextProvider("Provider 2", "Info 2"),
        },
    )

    expected_prompt = """# IDENTITY and PURPOSE
- Background info

# INTERNAL ASSISTANT STEPS
- Step 1

# OUTPUT INSTRUCTIONS
- Custom instruction
- Always respond using the proper JSON schema.
- Always use the available additional information and context to enhance the response.

# EXTRA INFORMATION AND CONTEXT
## Provider 1
Info 1

## Provider 2
Info 2"""

    assert generator.generate_prompt() == expected_prompt


def test_generate_prompt_with_empty_sections():
    generator = SystemPromptGenerator(background=[], steps=[], output_instructions=[])

    expected_prompt = """# IDENTITY and PURPOSE
- This is a conversation with a helpful and friendly AI assistant.

# OUTPUT INSTRUCTIONS
- Always respond using the proper JSON schema.
- Always use the available additional information and context to enhance the response."""

    assert generator.generate_prompt() == expected_prompt


def test_context_provider_repr():
    provider = MockContextProvider("Test Provider", "Test Info")
    assert repr(provider) == "Test Info"


def test_generate_prompt_with_empty_context_provider():
    empty_provider = MockContextProvider("Empty Provider", "")
    generator = SystemPromptGenerator(background=["Background"], context_providers={"empty": empty_provider})

    expected_prompt = """# IDENTITY and PURPOSE
- Background

# OUTPUT INSTRUCTIONS
- Always respond using the proper JSON schema.
- Always use the available additional information and context to enhance the response.

# EXTRA INFORMATION AND CONTEXT"""

    assert generator.generate_prompt() == expected_prompt
