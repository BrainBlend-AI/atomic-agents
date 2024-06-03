from typing import Type, Optional
from pydantic import BaseModel

class BaseTool:
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    def __init__(self, tool_description_override: Optional[str] = None):
        self.tool_name = self.input_schema.Config.title
        self.tool_description = tool_description_override or self.input_schema.Config.description

    def run(self, params: BaseModel) -> BaseModel:
        raise NotImplementedError("Subclasses should implement this method")