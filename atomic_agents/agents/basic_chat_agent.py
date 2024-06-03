import os
from groq import Groq
import instructor
import openai
from pydantic import BaseModel, Field
from datetime import datetime
from atomic_agents.lib.utils.logger import logger
from atomic_agents.lib.chat_memory import ChatMemory
from atomic_agents.lib.vectordb.chroma.manager import ChromaDBDocumentManager
from atomic_agents.tools.vectordb_query_tool import VectorDBQueryTool

class BasicChatAgentInputSchema(BaseModel):
    chat_input: str = Field(..., description="The input text for the chat agent.")

class BasicChatAgentResponse(BaseModel):
    response: str = Field(..., description='The response from the chat agent.')

class BasicChatAgent:
    def __init__(self, client, model: str = "gpt-3.5-turbo", agent_background: str = "You are a helpful AI assistant.", initial_message: str = None, initial_memory: list = [], vector_db = None, include_context_in_system_prompt: bool = False, input_schema = None, output_schema = None):
        self.input_schema = input_schema or BasicChatAgentInputSchema
        self.output_schema = output_schema or BasicChatAgentResponse
        
        self.client = client
        self.model = model
        self.agent_background = agent_background
        self.memory = ChatMemory()
        self.include_context_in_system_prompt = include_context_in_system_prompt
        
        self.vector_db = vector_db
        
        if initial_memory:
            self.memory.load_from_dict_list(initial_memory)
            
        if initial_message:
            self.memory.add_message("assistant", initial_message)

    def get_system_prompt(self) -> str:
        current_date = datetime.now().isoformat()
        system_prompt = (
            f"{self.agent_background}\n"
            "\n"
            f"The current date, in ISO format, is {current_date}.\n"
        )
        
        if self.vector_db and self.include_context_in_system_prompt:
            system_prompt += (
                f"The AI has access to the following context to answer questions. If certain context is irrelevant to the question, the AI will ignore it.\n"
                f"Context:\n"
            )
            
            for i, document in enumerate(self.vector_db.run(self.vector_db.input_schema(queries=[self.memory.get_history()[-1].content])).results):
                system_prompt += f"Document {i}. {document.metadata['url']}\n"
                system_prompt += f"====================\n"
                system_prompt += f"{document.content}\n"
                system_prompt += f"====================\n\n"
        return system_prompt

    def get_response(self, response_model=None) -> BaseModel:
        if response_model is None:
            response_model = self.output_schema
        
        messages = [{"role": "system", "content": self.get_system_prompt()}] + self.memory.get_history()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=response_model
        )
        return response


    def run(self, user_input: str) -> str:
        self.memory.add_message("user", user_input)
        response = self.get_response(response_model=self.output_schema)
        self.memory.add_message("assistant", response.model_dump_json())
        return response
    
    
if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    
    openai_client = openai.OpenAI()
    client = instructor.from_openai(openai_client)
    model = "gpt-3.5-turbo"
    groq_client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")))
    groq_model = os.getenv("GROQ_CHAT_MODEL")
    initial_message = "Hello! How can I assist you today?"

    db = VectorDBQueryTool(db_path='chromadb_persist', collection_name='brainblendai.com', max_results=3)
    agent = BasicChatAgent(
        client=groq_client, 
        model=groq_model, 
        initial_message=initial_message,
        agent_background="You are an AI assistant that, whatever the user input, will provide an answer in Alexandrine verse.",
        vector_db=db,
        include_context_in_system_prompt=False
    )
    console.print(f'Agent: {initial_message}')

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chat...")
            break

        response = agent.run(user_input)
        console.print(f"Agent: {response.response}")
