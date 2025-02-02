import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from rag_chatbot.config import ChatConfig


class RAGQuestionAnsweringAgentInputSchema(BaseIOSchema):
    """Input schema for the RAG QA agent."""

    question: str = Field(..., description="The user's question to answer")


class RAGQuestionAnsweringAgentOutputSchema(BaseIOSchema):
    """Output schema for the RAG QA agent."""

    answer: str = Field(..., description="The answer to the user's question based on the retrieved context")


qa_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert at answering questions using retrieved context chunks from a RAG system.",
                "Your role is to synthesize information from the chunks to provide accurate, well-supported answers.",
                "You must explain your reasoning process before providing the answer.",
            ],
            steps=[
                "1. Analyze the question and available context chunks",
                "2. Identify the most relevant information in the chunks",
                "3. Explain how you'll use this information to answer the question",
                "4. Synthesize information into a coherent answer",
            ],
            output_instructions=[
                "First explain your reasoning process clearly",
                "Then provide a clear, direct answer based on the context",
                "If context is insufficient, state this in your reasoning",
                "Never make up information not present in the chunks",
                "Focus on being accurate and concise",
            ],
        ),
        input_schema=RAGQuestionAnsweringAgentInputSchema,
        output_schema=RAGQuestionAnsweringAgentOutputSchema,
    )
)
