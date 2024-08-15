# File: outline_agent.py

import instructor
import openai
from pydantic import BaseModel, Field
from typing import List
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator


class Question(BaseModel):
    question: str = Field(..., description="The question to answer in this section or subsection")
    potential_sources: List[str] = Field(
        default_factory=list, description="URLs of potential sources or references for this question. Required. Min. 1."
    )


class OutlineSubSection(BaseModel):
    title: str = Field(..., description="The title of the outline subsection")
    questions_to_answer: List[Question] = Field(
        default_factory=list,
        description="A list of 2-4 hypothetical questions that the contents of this subsection should answer.",
    )


class OutlineSection(BaseModel):
    title: str = Field(..., description="The title of the outline section")
    questions_to_answer: List[Question] = Field(
        default_factory=list, description="2-3 overarching questions to answer in this section"
    )
    subsections: List[OutlineSubSection] = Field(
        default_factory=list, description="Subsections of this outline section. Each section must have 3-5 subsections."
    )


class OutlineAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the OutlineAgent."""

    topic: str = Field(..., description="The main topic of the article")


class OutlineAgentOutputSchema(BaseIOSchema):
    """This schema defines the output schema for the OutlineAgent."""

    internal_reasoning: List[str] = Field(
        ...,
        description="Internal reasoning about the context and what information it contains that could be useful in generating or modifying an outline.",
    )
    title: str = Field(..., description="The title of the article")
    outline: List[OutlineSection] = Field(
        ..., description="The generated or modified outline. The outline must have 5-7 main sections."
    )


# Create the outline agent
outline_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert AI outline creator and editor, specializing in creating comprehensive and well-structured outlines.",
                "Your task is to generate or modify article outlines based on the given topic and context, ensuring a logical flow and thorough coverage of the subject.",
            ],
            steps=[
                "Analyze the given topic and any additional context provided in depth.",
                "Create a comprehensive structure for the article with 5-7 main sections.",
                "For each main section, develop 3-5 subsections that explore different aspects of the main section's topic.",
                "Ensure the outline is well-organized, logical, and covers all important aspects of the topic in a balanced manner.",
                "For each section, provide 2-3 overarching questions to answer.",
                "For each subsection, provide 2-4 specific questions to answer, including potential sources for each question.",
            ],
            output_instructions=[
                "Create a clear, concise, and comprehensive outline with 5-7 main sections.",
                "Ensure each main section has 3-5 well-defined subsections.",
                "Provide 1-2 overarching questions for each main section.",
                "Include 2-4 specific questions to answer for each subsection, along with potential sources.",
                "Use descriptive and informative titles for each section and subsection.",
                "Ensure each section and subsection is relevant to the main topic and contributes to a cohesive narrative.",
                "Aim for a balanced structure that covers the topic comprehensively, with appropriate depth in each section.",
            ],
        ),
        input_schema=OutlineAgentInputSchema,
        output_schema=OutlineAgentOutputSchema,
    )
)
