from pydantic import BaseModel, Field
from atomic_agents.agents.base_agent import BaseIOSchema
import instructor
import openai
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

class RefineAnswerInputSchema(BaseIOSchema):
    question: str = Field(..., description='The question that was asked.')
    answer: str = Field(..., description='The initial answer to the question.')

class RefineAnswerOutputSchema(BaseModel):
    refined_answer: str = Field(..., description='The refined answer to the question.')

# Create the refine answer agent
refine_answer_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()), 
        model='gpt-3.5-turbo',
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an intelligent answer refinement expert.",
                "Your task is to expand and elaborate on an existing answer to a question using additional context from vector DB chunks."
            ],
            steps=[
                "You will receive a question or instruction, the initial answer, and additional context from vector DB chunks.",
                "Correct any inaccuracies and factual errors in the initial answer.",
                "Expand and elaborate on the initial answer using the additional context to provide a more comprehensive and detailed response."
            ],
            output_instructions=[
                "Ensure the refined answer is clear, concise, and well-structured.",
                "Ensure the refined answer is directly relevant to the question and incorporates the additional context provided.",
                "Add new information and details to make the final answer more elaborate and informative.",
                "Do not make up any new information; only use the information present in the context."
            ]
        ),
        input_schema=RefineAnswerInputSchema,
        output_schema=RefineAnswerOutputSchema
    )
)