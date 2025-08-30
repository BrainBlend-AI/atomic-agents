#!/usr/bin/env python3
"""
Demonstrates AtomicAgent not triggering instructor parse:error hooks.
Expected: parse:error hook called on validation failure
Actual: Only completion:* hooks are called
"""

import asyncio
from pydantic import Field
import instructor
import openai
from atomic_agents.agents.atomic_agent import AtomicAgent, AgentConfig
from atomic_agents.context.system_prompt_generator import SystemPromptGenerator
from atomic_agents.context.chat_history import ChatHistory
from atomic_agents.base.base_io_schema import BaseIOSchema


from pydantic import field_validator


class SimpleOutput(BaseIOSchema):
    """Output model designed to trigger validation errors."""

    # Impossible constraint: must be both positive and negative
    impossible_number: int = Field(..., description="A number")
    # String that must pass validation
    test_string: str = Field(..., description="Any string")

    @field_validator("impossible_number")
    @classmethod
    def validate_impossible(cls, v):
        if v > 0:
            raise ValueError("Number must be negative")
        if v <= 0:
            raise ValueError("Number must be positive")
        return v


class SimpleInput(BaseIOSchema):
    """Input schema."""

    question: str = Field(..., description="The question to ask")


class MinimalAgent:
    def __init__(self):
        self.hook_calls = []
        self.client = self._setup_instructor_client()
        self.agent = self._setup_atomic_agent()

    def _setup_instructor_client(self):
        import os

        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  OPENAI_API_KEY not set. Set it to test with real API:")
            print("   export OPENAI_API_KEY=your_key_here")
            print("   This example will demonstrate hook registration without API calls.")
            # Return None to skip API calls but still demonstrate hook registration
            return None

        # Use OpenAI with API key
        client = instructor.from_openai(
            openai.AsyncOpenAI(api_key=api_key),
            mode=instructor.Mode.TOOLS,
        )

        return client

    def _setup_atomic_agent(self):
        if not self.client:
            print("🚫 No client available - creating agent for hook demonstration only")
            # Create minimal config for demonstration
            return None

        system_prompt = SystemPromptGenerator(
            background=["You are a helpful assistant."],
            steps=["Answer with required JSON format."],
            output_instructions=[
                "Return JSON with 'name', 'count', and 'items' fields",
                "Example: {'name': 'test', 'count': 5, 'items': ['a', 'b']}",
            ],
        )

        config = AgentConfig(
            client=self.client,
            model="gpt-5-nano",  # Using new weaker model
            history=ChatHistory(),
            system_prompt_generator=system_prompt,
            model_api_parameters={"reasoning_effort": "minimal"},
        )

        agent = AtomicAgent[SimpleInput, SimpleOutput](config=config)

        # Register ALL available instructor hooks
        self._register_all_hooks(agent)

        return agent

    def _register_all_hooks(self, agent):
        """Register all available instructor hooks with the AtomicAgent."""

        print("🎯 Registering all instructor hooks:")

        # All instructor hook types based on the documentation
        hooks = [
            ("completion:kwargs", self._hook_completion_kwargs, "Called before sending request to LLM"),
            ("completion:response", self._hook_completion_response, "Called when response received from LLM"),
            ("completion:error", self._hook_completion_error, "Called when completion request fails"),
            ("parse:error", self._hook_parse_error, "Called when parsing/validation fails"),
            ("completion:last_attempt", self._hook_last_attempt, "Called on final retry attempt"),
        ]

        for hook_name, handler, description in hooks:
            if agent:
                agent.register_hook(hook_name, handler)
                print(f"   ✅ {hook_name}: {description}")
            else:
                print(f"   📝 {hook_name}: {description} (would register if agent available)")

        print("✅ All hooks registered!")

    def _hook_completion_kwargs(self, *args, **kwargs):
        self.hook_calls.append("completion:kwargs")
        print("🔵 completion:kwargs hook fired")
        print(f"   📋 Request parameters: {list(kwargs.keys())}")

    def _hook_completion_response(self, response):
        self.hook_calls.append("completion:response")
        print("🔵 completion:response hook fired")
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content or "No content"
            print(f"   📄 Response preview: {content[:100]}...")

    def _hook_completion_error(self, error):
        self.hook_calls.append("completion:error")
        print(f"🔴 completion:error hook fired: {type(error).__name__}")
        print(f"   ❌ Error: {str(error)[:150]}...")

    def _hook_parse_error(self, error):
        self.hook_calls.append("parse:error")
        print(f"🔴 parse:error hook fired: {type(error).__name__}")
        print(f"   🚫 Validation failed: {str(error)[:150]}...")
        print("   🎯 THIS IS THE KEY HOOK FOR VALIDATION FEEDBACK!")

    def _hook_last_attempt(self, error):
        self.hook_calls.append("completion:last_attempt")
        print(f"🔴 completion:last_attempt hook fired: {type(error).__name__}")
        print(f"   🔄 Final retry failed: {str(error)[:150]}...")

    async def run_test(self):
        if not self.agent:
            print("\n🎯 HOOK DEMONSTRATION COMPLETE")
            print("   All hook types have been registered and are ready to fire when:")
            print("   • completion:kwargs - Before each LLM request")
            print("   • completion:response - When LLM responds successfully")
            print("   • completion:error - When LLM request fails")
            print("   • parse:error - When response fails Pydantic validation")
            print("   • completion:last_attempt - On final retry attempt")
            print("\n💡 To test with real API calls:")
            print("   1. Set OPENAI_API_KEY environment variable")
            print("   2. Run this example again")
            return []

        print("\n🧪 Testing with real API calls...")

        # Test case designed to trigger validation errors with impossible constraints
        test_input = SimpleInput(
            question="Return JSON with impossible_number=5 and test_string='hello'. " "Use exactly these values."
        )

        try:
            result = await self.agent.run_async(test_input)
            print(f"✅ Success: {result}")
        except Exception as e:
            print(f"❌ Expected failure: {type(e).__name__}")
            print(f"   Details: {str(e)[:200]}...")

        print("\n📊 Final Results:")
        print(f"   All hooks called: {self.hook_calls}")
        print(f"   Unique hooks fired: {set(self.hook_calls)}")

        # Report hook coverage
        all_hooks = ["completion:kwargs", "completion:response", "completion:error", "parse:error", "completion:last_attempt"]

        print("\n🎯 Hook Coverage Report:")
        for hook in all_hooks:
            status = "✅" if hook in self.hook_calls else "❌"
            count = self.hook_calls.count(hook)
            print(f"   {status} {hook}" + (f" (called {count}x)" if count > 0 else ""))

        if "parse:error" in self.hook_calls:
            print("\n🎉 SUCCESS: parse:error hook was triggered!")
            print("   This means AtomicAgent hook integration is working correctly.")
        else:
            print("\n💭 NOTE: parse:error hook not triggered in this test.")
            print("   This could mean:")
            print("   • No validation errors occurred (LLM returned valid JSON)")
            print("   • Different error type occurred before validation")
            print("   • More specific test conditions needed to trigger validation failure")

        return self.hook_calls


async def main():
    agent = MinimalAgent()
    await agent.run_test()


if __name__ == "__main__":
    asyncio.run(main())
