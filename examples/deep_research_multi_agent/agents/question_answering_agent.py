import instructor
import openai
from pydantic import BaseModel, Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo

class AnswerAgentInputSchema(BaseIOSchema):
    question: str = Field(..., description='A question that needs to be answered based on the provided context.')

class AnswerAgentOutputSchema(BaseIOSchema):
    markdown_output: str = Field(..., description='The answer to the question in markdown format.')

# Create the answer agent
answer_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()), 
        model='gpt-3.5-turbo',
        system_prompt_generator=SystemPromptGenerator(
            SystemPromptInfo(
                background=[
                    "You are an intelligent answering expert.",
                    "Your task is to provide accurate and detailed answers to user questions based on the given context."
                ],
                steps=[
                    "You will receive a question and the context information.",
                    "Generate a detailed and accurate answer based on the context."
                ],
                output_instructions=[
                    "Ensure clarity and conciseness in each answer.",
                    "Ensure the answer is directly relevant to the question and context provided."
                ]
            )
        ),
        input_schema=AnswerAgentInputSchema,
        output_schema=AnswerAgentOutputSchema
    )
)