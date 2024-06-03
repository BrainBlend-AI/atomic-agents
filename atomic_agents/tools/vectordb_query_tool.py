import os
from pydantic import BaseModel, Field
from typing import List, Optional
from rich.console import Console
import openai
import instructor

from atomic_agents.tools.base import BaseTool
from atomic_agents.lib.vectordb.chroma.manager import ChromaDBDocumentManager
from atomic_agents.lib.models.web_document import Document

################
# INPUT SCHEMA #
################
class VectorDBQueryToolSchema(BaseModel):
    queries: List[str] = Field(..., description="List of 3 queries to query the vector database.")

    class Config:
        title = "VectorDBQueryTool"
        description = "Tool for querying the Chroma VectorDB."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class VectorDBQueryResultSchema(BaseModel):
    content: str
    metadata: Optional[dict] = None

class VectorDBQueryToolOutputSchema(BaseModel):
    results: List[VectorDBQueryResultSchema]

##############
# TOOL LOGIC #
##############
class VectorDBQueryTool(BaseTool):
    input_schema = VectorDBQueryToolSchema
    output_schema = VectorDBQueryToolOutputSchema

    def __init__(self, db_path: str, collection_name: str, tool_description_override: Optional[str] = None, max_results: int = 10):
        super().__init__(tool_description_override)
        self.db_path = db_path
        self.collection_name = collection_name
        self.max_results = max_results
        self.manager = ChromaDBDocumentManager(db_path, collection_name)

    def run(self, params: VectorDBQueryToolSchema) -> VectorDBQueryToolOutputSchema:
        documents = self.manager.query_documents(params.queries, self.max_results)
        results = [VectorDBQueryResultSchema(content=doc.content, metadata=doc.metadata.model_dump()) for doc in documents]
        return VectorDBQueryToolOutputSchema(results=results)

#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()

    # Initialize the client outside
    client = instructor.from_openai(
        openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    )

    # Extract structured data from natural language
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=VectorDBQueryTool.input_schema,
        messages=[
            {"role": "system", "content": "This AI generates 3 queries that can be used to gather context to help with reacting to the user input."}, 
            {"role": "user", "content": "What does the describeit tool do?"}
        ],
    )

    # Print the result
    output = VectorDBQueryTool(db_path="chromadb_persist", collection_name="brainblendai.com", max_results=3).run(result)
    for i, result in enumerate(output.results):
        rich_console.print(f"{i}. Content: {result.content}, Metadata: {result.metadata}")