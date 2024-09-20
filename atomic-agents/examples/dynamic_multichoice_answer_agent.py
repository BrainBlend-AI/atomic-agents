# File: multiple_choice_agent.py

import instructor
import openai
from pydantic import BaseModel, Field, create_model
from typing import List, Dict, Any, Literal, Union
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator


class Question(BaseModel):
    question: str = Field(..., description="The multiple-choice question")
    options: List[str] = Field(..., min_items=2, description="List of possible answer options")


class MultipleChoiceAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the MultipleChoiceAgent."""

    questions: List[Question] = Field(..., min_items=1, description="List of multiple-choice questions")
    context: str = Field(..., description="Additional context or information to help answer the questions")


def create_dynamic_output_schema(question: Question):
    field_name = "answer"
    options_literal = Literal[tuple(question.options)]
    fields = {
        # "step_by_step_reasoning": (List[str], Field(..., description="Step-by-step reasoning for the answer")),
        field_name: (options_literal, Field(..., description=f"Answer for question: {question.question}")),
    }
    return create_model(f"DynamicMultipleChoiceOutput_{id(question)}", **fields)


def run_multiple_choice_agent(questions: List[Question], context: str):
    results = {}

    for i, question in enumerate(questions):
        # Create a dynamic output schema for each question
        dynamic_output_schema = create_dynamic_output_schema(question)

        # Update the agent's output schema with the dynamic schema for this question
        multiple_choice_agent.output_schema = dynamic_output_schema

        # Create a single-question input for the agent
        single_question_input = MultipleChoiceAgentInputSchema(questions=[question], context=context)

        # Run the agent for this question
        result = multiple_choice_agent.run(single_question_input)

        # Store the result
        results[f"question_{i+1}"] = {"answer": result.answer, "reasoning": "result.step_by_step_reasoning"}

    return results


# Create the multiple choice agent
multiple_choice_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",  # Updated to a more recent model
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert AI multiple-choice question answering system.",
                "Your task is to provide accurate answers to multiple-choice questions based on the given context and options.",
            ],
            steps=[
                "Analyze each question and its options carefully.",
                "Consider the provided context to inform your decision.",
                "Develop a step-by-step reasoning process for your answer.",
                "Select the most appropriate answer for each question based on the context and options.",
                "Provide clear and concise answers along with your reasoning.",
            ],
            output_instructions=[
                "For each question, select the best answer from the provided options.",
                "Provide a list of step-by-step reasoning points that led to your answer.",
                "Ensure your answers and reasoning are directly relevant to the questions and context.",
                "Format your output as requested, with both the selected answer and the step-by-step reasoning.",
            ],
        ),
        input_schema=MultipleChoiceAgentInputSchema,
        output_schema=None,  # We will set this dynamically
    )
)


# Example usage
if __name__ == "__main__":
    questions = [
        Question(question="What is the capital of Egypt?", options=["London", "Berlin", "Paris", "Cairo", "Madrid"]),
        Question(question="Which planet is known as the Red Planet?", options=["Venus", "Mars", "Jupiter", "Saturn"]),
        Question(
            question="Who wrote 'To Kill a Mockingbird'?",
            options=["Ernest Hemingway", "Harper Lee", "F. Scott Fitzgerald", "John Steinbeck"],
        ),
        Question(question="Is the Earth flat?", options=["Yes", "No"]),
        Question(
            question="What is the largest mammal on Earth?",
            options=["African Elephant", "Blue Whale", "Giraffe", "Hippopotamus"],
        ),
        Question(
            question="Who was the first person to step on the Moon?",
            options=["Yuri Gagarin", "Neil Armstrong", "Buzz Aldrin", "John Glenn"],
        ),
        # New complex questions
        Question(
            question="What is the capital of Burkina Faso?",
            options=["Ouagadougou", "Bamako", "Niamey", "Accra", "Lomé"],
        ),
        Question(
            question="Is JavaScript a compiled or interpreted language?",
            options=["Compiled", "Interpreted", "Both", "Neither"],
        ),
        Question(
            question="Who painted 'The Persistence of Memory'?",
            options=["Pablo Picasso", "Salvador Dalí", "Vincent van Gogh", "Claude Monet"],
        ),
        Question(
            question="What is the primary function of mitochondria in a cell?",
            options=["Energy production", "Protein synthesis", "Cell division", "Waste removal"],
        ),
        Question(question="Does the moon have its own light source?", options=["Yes", "No"]),
        Question(
            question="Which of these is not a programming paradigm?",
            options=["Object-Oriented", "Functional", "Imperative", "Alphabetical"],
        ),
        Question(
            question="What is the capital of Canada?",
            options=["Toronto", "Vancouver", "Montreal", "Ottawa", "Quebec City"],
        ),
        Question(
            question="Who wrote '1984'?",
            options=["George Orwell", "Aldous Huxley", "Ray Bradbury", "Philip K. Dick"],
        ),
        Question(
            question="What is the largest planet in our solar system?",
            options=["Earth", "Mars", "Jupiter", "Saturn"],
        ),
        Question(
            question="Which of these is not a type of cloud?",
            options=["Cumulus", "Stratus", "Nimbus", "Nebulus"],
        ),
    ]
    context = """
    Egypt's capital is Cairo. Mars is often called the Red Planet due to its reddish appearance.
    Harper Lee wrote the classic novel 'To Kill a Mockingbird'. The Earth is not flat; it is an oblate spheroid.
    The Blue Whale is the largest animal known to have ever existed. Neil Armstrong was the first person to walk on the Moon in 1969.
    Ouagadougou is the capital of Burkina Faso. JavaScript is primarily an interpreted language, although modern engines use just-in-time compilation.
    Salvador Dalí painted 'The Persistence of Memory'. Mitochondria are often referred to as the powerhouses of the cell due to their role in energy production.
    The moon does not have its own light source; it reflects sunlight. Ottawa is the capital city of Canada.
    George Orwell wrote the dystopian novel '1984'. Jupiter is the largest planet in our solar system.
    """

    answers = run_multiple_choice_agent(questions, context)
    for i, (question_num, result) in enumerate(answers.items()):
        print(f"\n{question_num}:")
        print(f"\n{question_num}:")
        print(f"Question: {questions[i].question}")
        print(f"Options: {questions[i].options}")
        print(f"Answer: {result['answer']}")
        # print("Reasoning:")
        # for step in result["reasoning"]:
        #     print(f"- {step}")
