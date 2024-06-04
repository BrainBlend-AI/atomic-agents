import os
from pydantic import BaseModel, Field
from typing import Optional
from rich.console import Console
import openai
import instructor

from atomic_agents.lib.tools.base import BaseTool

################
# INPUT SCHEMA #
################
class UserInputToolSchema(BaseModel):
    question: str = Field(..., description="The question to ask the user.")
    context: Optional[str] = Field(None, description="Additional context or information to provide to the user.")

    class Config:
        title = "UserInputTool"
        description = "Tool for asking clarifying questions to the user. Use this tool when the AI needs more information or clarification from the user."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class UserInputToolOutputSchema(BaseModel):
    answer: str = Field(..., description="The user's answer to the question.")

##############
# TOOL LOGIC #
##############
class UserInputTool(BaseTool):
    input_schema = UserInputToolSchema
    output_schema = UserInputToolOutputSchema
    
    def __init__(self, tool_description_override: Optional[str] = None):
        super().__init__(tool_description_override)

    def run(self, params: UserInputToolSchema) -> UserInputToolOutputSchema:
        print(f"Question: {params.question}")
        if params.context:
            print(f"Context: {params.context}")
        answer = input("Your answer: ")
        return UserInputToolOutputSchema(answer=answer)

#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    
    question = "What is your favorite color?"
    
    user_input_tool = UserInputTool()
    user_input_params = UserInputToolSchema(question=question)
    user_input_output = user_input_tool.run(user_input_params)
    
    rich_console.print(f"User's answer: {user_input_output.answer}")