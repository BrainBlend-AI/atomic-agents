from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
import instructor
import openai
from pydantic import Field, BaseModel
from typing import List, Union, Any, Optional
import os
import json


class NutritionFacts(BaseIOSchema):
    """Represents nutrition facts from a food label"""

    serving_size: str = Field(..., description="Serving size information")
    servings_per_container: float = Field(..., description="Number of servings per container")
    calories: int = Field(..., description="Calories per serving")
    total_fat: float = Field(..., description="Total fat in grams")
    saturated_fat: float = Field(..., description="Saturated fat in grams")
    trans_fat: float = Field(..., description="Trans fat in grams")
    cholesterol: int = Field(..., description="Cholesterol in milligrams")
    sodium: int = Field(..., description="Sodium in milligrams")
    total_carbohydrates: float = Field(..., description="Total carbohydrates in grams")
    dietary_fiber: float = Field(..., description="Dietary fiber in grams")
    total_sugars: float = Field(..., description="Total sugars in grams")
    added_sugars: float = Field(..., description="Added sugars in grams")
    protein: float = Field(..., description="Protein in grams")
    vitamin_d: float = Field(..., description="Vitamin D in micrograms")
    calcium: int = Field(..., description="Calcium in milligrams")
    iron: float = Field(..., description="Iron in milligrams")
    potassium: int = Field(..., description="Potassium in milligrams")


class ImageMessage(BaseModel):
    """A message that can contain multiple images"""

    text: str
    image_paths: List[str]

    def to_content(self):
        """Convert to the format expected by the API"""
        return [self.text, *[instructor.Image.from_path(path) for path in self.image_paths]]

    def model_dump(self, *args, **kwargs):
        """Custom serialization that only includes the text and paths"""
        return {"text": self.text, "image_paths": [str(path) for path in self.image_paths]}


class NutritionInputSchema(BaseIOSchema):
    """Schema for nutrition facts input"""

    message: ImageMessage

    def get_api_messages(self):
        """Get the messages in the format expected by the API"""
        return self.message.to_content()


class NutritionOutputSchema(BaseIOSchema):
    """Schema for nutrition facts extraction from multiple images"""

    nutrition_facts: List[NutritionFacts] = Field(..., description="Nutrition facts extracted from each image")


# Monkey patch the get_history method to handle our custom message format
original_get_history = AgentMemory.get_history


def patched_get_history(self):
    history = []
    for message in self.history:
        if isinstance(message.content, NutritionInputSchema) and message.role == "user":
            # For our custom input schema, use the API format
            history.append({"role": message.role, "content": message.content.get_api_messages()})
        else:
            # For other messages, use the normal serialization
            history.append({"role": message.role, "content": json.dumps(message.content.model_dump())})
    return history


AgentMemory.get_history = patched_get_history

# Set up the system prompt
system_prompt_generator = SystemPromptGenerator(
    background=[
        "You are an expert at extracting nutrition information from food labels.",
        "You can accurately read and parse nutrition facts panels from images.",
        "You understand serving sizes, measurements, and nutritional content.",
        "You can process multiple nutrition labels from multiple images.",
    ],
    steps=[
        "For each image:",
        "1. Identify the nutrition facts panel",
        "2. Extract all nutritional values and serving information",
        "3. Convert all values to their appropriate units",
        "4. Add the nutrition facts to the output list",
    ],
    output_instructions=[
        "For each nutrition label image:",
        "1. Extract serving size and servings per container",
        "2. Record all nutritional values in their specified units",
        "3. Ensure accuracy of measurements and conversions",
        "Return all nutrition facts in the list",
    ],
)

# Initialize the agent
agent = BaseAgent(
    config=BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",
        system_prompt_generator=system_prompt_generator,
        memory=AgentMemory(),
        output_schema=NutritionOutputSchema,
    )
)


def main():
    print("Starting nutrition facts extraction...")
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the basic-multimodal directory and then to test_images
    image_dir = os.path.join(os.path.dirname(script_dir), "test_images")
    image_paths = [os.path.join(image_dir, "nutrition_label_2.jpg")]
    print(f"Image paths: {image_paths}")

    # Create the message with the image
    message = ImageMessage(
        text="Extract all nutrition information from these food labels. Include serving size, calories, and all nutrient values.",
        image_paths=[str(path) for path in image_paths],
    )

    # Create input schema with the message
    input_schema = NutritionInputSchema(message=message)
    print("Created input schema with images")

    # Add the message to memory
    agent.memory.add_message("user", input_schema)
    print("Added message to memory")

    try:
        # Get response
        print("Getting response...")
        response = agent.get_response()
        print("Got response successfully")

        for i, facts in enumerate(response.nutrition_facts, 1):
            print(f"\nNutrition Facts {i}:")
            print(f"Serving Size: {facts.serving_size}")
            print(f"Servings Per Container: {facts.servings_per_container}")
            print(f"Calories: {facts.calories}")
            print(f"Total Fat: {facts.total_fat}g")
            print(f"Saturated Fat: {facts.saturated_fat}g")
            print(f"Trans Fat: {facts.trans_fat}g")
            print(f"Cholesterol: {facts.cholesterol}mg")
            print(f"Sodium: {facts.sodium}mg")
            print(f"Total Carbohydrates: {facts.total_carbohydrates}g")
            print(f"Dietary Fiber: {facts.dietary_fiber}g")
            print(f"Total Sugars: {facts.total_sugars}g")
            print(f"Added Sugars: {facts.added_sugars}g")
            print(f"Protein: {facts.protein}g")
            print(f"Vitamin D: {facts.vitamin_d}mcg")
            print(f"Calcium: {facts.calcium}mg")
            print(f"Iron: {facts.iron}mg")
            print(f"Potassium: {facts.potassium}mg")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
