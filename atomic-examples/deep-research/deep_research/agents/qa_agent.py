import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from deep_research.config import ChatConfig


class QuestionAnsweringAgentInputSchema(BaseIOSchema):
    """This is the input schema for the QuestionAnsweringAgent."""

    question: str = Field(..., description="The question to answer.")


class QuestionAnsweringAgentOutputSchema(BaseIOSchema):
    """This is the output schema for the QuestionAnsweringAgent."""

    answer: str = Field(..., description="The answer to the question.")
    follow_up_questions: list[str] = Field(
        ...,
        description=(
            "Specific questions about the topic that would help the user learn more details about the subject matter. "
            "For example, if discussing a Nobel Prize winner, suggest questions about their research, impact, or "
            "related scientific concepts."
        ),
    )


question_answering_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert question answering agent focused on providing factual information and encouraging deeper topic exploration.",
                "For general greetings or non-research questions, provide relevant questions about the system's capabilities and research functions.",
            ],
            steps=[
                "Analyze the question and identify the core topic",
                "Answer the question using available information",
                "For topic-specific questions, generate follow-up questions that explore deeper aspects of the same topic",
                "For general queries about the system, suggest questions about research capabilities and functionality",
            ],
            output_instructions=[
                "Answer in a direct, informative manner",
                "NEVER generate generic conversational follow-ups like 'How are you?' or 'What would you like to know?'",
                "For topic questions, follow-up questions MUST be about specific aspects of that topic",
                "For system queries, follow-up questions should be about specific research capabilities",
                "Example good follow-ups for a Nobel Prize question:",
                "- What specific discoveries led to their Nobel Prize?",
                "- How has their research influenced their field?",
                "- What other scientists collaborated on this research?",
                "Example good follow-ups for system queries:",
                "- What types of sources do you use for research?",
                "- How do you verify information accuracy?",
                "- What are the limitations of your search capabilities?",
            ],
        ),
        input_schema=QuestionAnsweringAgentInputSchema,
        output_schema=QuestionAnsweringAgentOutputSchema,
    )
)
