import instructor
import openai
from pydantic import BaseModel, Field
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator


class QuestionAnsweringAgentInputSchema(BaseModel):
    question: str = Field(..., description="The question to be answered")


class QuestionAnsweringAgentOutputSchema(BaseModel):
    answer: str = Field(..., description="The answer to the provided question")


# Create the question answering agent
question_answering_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert AI question answering system.",
                "Your task is to provide accurate and concise answers to questions based on the given context.",
            ],
            steps=[
                "Analyze the provided question and context.",
                "Search the context for relevant information.",
                "Generate a clear and concise answer based on the context.",
                "Identify the sources used for the answer.",
            ],
            output_instructions=[
                "Provide an accurate answer to the question.",
                "Ensure the answer is directly relevant to the question.",
                "Include sources for the answer when available.",
                "Keep the answer concise but informative.",
            ],
        ),
        input_schema=QuestionAnsweringAgentInputSchema,
        output_schema=QuestionAnsweringAgentOutputSchema,
    )
)
