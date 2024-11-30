import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from deep_research.config import ChatConfig


class ChoiceAgentInputSchema(BaseIOSchema):
    """Input schema for the ChoiceAgent."""

    user_message: str = Field(..., description="The user's latest message or question")
    decision_type: str = Field(..., description="Explanation of the type of decision to make")


class ChoiceAgentOutputSchema(BaseIOSchema):
    """Output schema for the ChoiceAgent."""

    reasoning: str = Field(..., description="Detailed explanation of the decision-making process")
    decision: bool = Field(..., description="The final decision based on the analysis")


choice_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a decision-making agent that determines whether a new web search is needed to answer the user's question.",
                "Your primary role is to analyze whether the existing context contains sufficient, up-to-date information to answer the question.",
                "You must output a clear TRUE/FALSE decision - TRUE if a new search is needed, FALSE if existing context is sufficient.",
            ],
            steps=[
                "1. Analyze the user's question for topic and information requirements",
                "2. Review the available context in scraped_content",
                "3. Check if the context is recent enough using current_date",
                "4. Determine if existing information is sufficient and relevant",
                "5. Make a binary decision: TRUE for new search, FALSE for using existing context",
            ],
            output_instructions=[
                "Your reasoning must clearly state WHY you need or don't need new information",
                "If the context is empty or irrelevant, always decide TRUE for new search",
                "If the question is time-sensitive, check current_date to ensure context is recent",
                "For ambiguous cases, prefer TRUE to gather fresh information",
                "IMPORTANT: Your decision must match your reasoning - don't contradict yourself",
            ],
        ),
        input_schema=ChoiceAgentInputSchema,
        output_schema=ChoiceAgentOutputSchema,
    )
)


if __name__ == "__main__":
    # Example usage for search decision
    search_example = choice_agent.run(
        ChoiceAgentInputSchema(user_message="Who won the nobel prize in physics in 2024?", decision_type="needs_search")
    )
    print(search_example)
