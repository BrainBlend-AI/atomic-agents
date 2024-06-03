from typing import List, Optional, Union
import instructor
import openai
from pydantic import BaseModel, Field, create_model
from datetime import datetime
from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent
from atomic_agents.lib.utils.format_tool_message import format_tool_message
from atomic_agents.lib.utils.logger import logger
from atomic_agents.lib.chat_memory import ChatMemory
from atomic_agents.tools.calculator_tool import CalculatorTool
from atomic_agents.tools.searx import SearxNGSearchTool
from atomic_agents.tools.user_input_tool import UserInputTool
from atomic_agents.tools.web_scraping_tool import WebScrapingTool

class OrchestratorAgentInputSchema(BaseModel):
    chat_input: str = Field(..., description="The input text for the chat agent.")

class MarkdownChatResponse(BaseModel):
    markdown: str = Field(..., description='The response from the chat agent to the user, in markdown format. ONLY use this when there are no more questions for the user and the task is complete.')

class TreeNode(BaseModel):
    """
    A node in a binary yes/no tree. The node can be the root node or a child node. A tree is at least 3 layers deep and should be a complete model with questions and results.
    This is used to determine which tool to use based on the input and the available tools.
    Tool names should be mentioned explicitly.
    """
    
    is_leaf_node: bool = Field(..., description="Whether the node is a leaf node.")
    result: Optional[str] = Field(None, description="The result of the tree if the node is a leaf node.", examples=["Use the calculator tool to perform the calculation.", "Use the SearXNG search tool to google for the latest gaming news", "Use the web scraping tool to scrape the website for the latest news."])
    question: Optional[str] = Field(None, description="The question to ask at this node.", examples=["Can the task be resolved with a web search, or does it require scraping?", "Does the task require a calculation, or is it a search for information?"])
    if_yes: Optional['TreeNode'] = Field(None, description="The node to follow if the answer to the question is 'yes'.")
    if_no: Optional['TreeNode'] = Field(None, description="The node to follow if the answer to the question is 'no'.")


class PlanningAgentResponse(BaseModel):
    """
    Response from the agent that details the next steps to take in the conversation based on the current state, available tools, and the agent's thought process.
    Tool names should be mentioned explicitly.
    """
    
    observation: str = Field(..., description="Observation/summary of the current state of the conversation.")
    analysis_tree: TreeNode = Field(..., description="Detailed analysis tree of the task and available tools to help determine the plan.")
    
    plan: List[str] = Field(..., description="The step-by-step plan to solve the task, based on the analysis tree. Must have at least 3 steps in the list.")

class OrchestratorAgentResponse(BaseModel):
    internal_thought: str = Field(..., description="Internal thought process involved in formulating the response or tool call.")
    
    response: Union[None] = Field(..., description='Response to the user or tool call from the orchestrator agent.')
    
    class Config:
        title = "OrchestratorAgentResponse"
        description = "Response from the orchestrator agent, which can either be a final answer response or a tool interface agent input."
        json_schema_extra = {
            "title": title,
            "description": description
        }


class OrchestratorAgent:
    def __init__(
            self, 
            client, 
            model: str = "gpt-3.5-turbo", 
            agent_background: str = "This is a conversation with a helpful AI assistant.", 
            initial_message: str = None, 
            initial_memory: list = [],
            available_tools: list = []
        ):
        self.client = client
        self.model = model
        self.agent_background = agent_background
        self.memory = ChatMemory()
        self.available_tools = available_tools
        
        if initial_memory:
            self.memory.load_from_dict_list(initial_memory)
            
        if initial_message:
            self.memory.add_message("assistant", initial_message)
            
        new_input_schema_union_list = []
        for tool in available_tools:
            new_input_schema_union_list.append(tool.input_schema)
        new_input_schema_union_list.append(MarkdownChatResponse)
        
        global OrchestratorAgentResponse
        OrchestratorAgentResponse = create_model(
            "OrchestratorAgentResponse",
            __base__=OrchestratorAgentResponse,
            response=(Union[tuple(new_input_schema_union_list)], Field(description='Response from the orchestrator agent, which can be a final answer response or a tool interface agent input.'))
        )
        logger.verbose(f"Created dynamic OrchestratorAgentResponse model with new input schema union list: {new_input_schema_union_list}")
            


    def get_system_prompt(self) -> str:
        current_date = datetime.now().isoformat()
        system_prompt = (
            f"{self.agent_background}\n"
            "\n"
            "This AI, when given a task, will always first analyze the task and determine which tool to use through a series of logical examinations and a decision tree.\n"
            "The AI will then generate a step-by-step plan to solve the task using the chosen tools and intermittently re-evaluate the plan based on the task and the tools.\n"
            f"The current date, in ISO format, is {current_date}."
        )
        
        if len(self.available_tools) > 0:
            system_prompt += "\n\nAvailable tools:"
        
        for tool in self.available_tools:
            system_prompt += f"\n- {tool.tool_name}: {tool.tool_description}"
        
        return system_prompt

    def get_response(self, response_model):
        messages = [{"role": "system", "content": self.get_system_prompt()}] + self.memory.get_history()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=response_model
        )
        return response

    def run(self, user_input: str) -> str:
        self.memory.add_message("user", f"Analyze and execute the plan for the following task: \"{user_input}\"")
        self.memory.add_message("assistant", self.get_response(PlanningAgentResponse).model_dump_json())
        response = self.get_response(response_model=OrchestratorAgentResponse)
        return self.handle_response(response)
    
    def handle_response(self, response):
        logger.verbose(f"Handling response: {response}")
        if isinstance(response.response, MarkdownChatResponse):
            self.memory.add_message("assistant", response.model_dump_json())
        else:
            tool_agent = None
            for agent in self.available_tools:
                if isinstance(response.response, agent.input_schema):
                    tool_agent = agent
                    break
            
            if tool_agent:
                tool_message = format_tool_message(response.response)
                logger.verbose(f"Formatted tool message: {tool_message}")
                tool_output = tool_agent.run(response.response)
                logger.verbose(f"Tool output: {tool_output}")
                self.memory.add_message("assistant", "", tool_message=tool_message)
                self.memory.add_message("tool", tool_output.model_dump_json(), tool_id=tool_message['id'])
                self.memory.add_message("assistant", self.get_response(PlanningAgentResponse).model_dump_json())
                response = self.get_response(OrchestratorAgentResponse)
                logger.verbose(f"ToolInterfaceAgent response: {response}")
                
                if not isinstance(response.response, MarkdownChatResponse):
                    return self.handle_response(response)
                
            else:
                self.memory.add_message("assistant", "I'm sorry, I couldn't understand your request.")
        return response

if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    
    # openai_client = openai.OpenAI(base_url="http://localhost:1234/v1")
    openai_client = openai.OpenAI()
    
    client = instructor.from_openai(openai_client)
    
    # Instantiate tool instances directly
    web_search_tool = SearxNGSearchTool(max_results=20)
    web_scraping_tool = WebScrapingTool()
    calculator_tool = CalculatorTool()
    user_input_tool = UserInputTool()
    
    # Instantiate agents with tool instances
    web_search_agent = ToolInterfaceAgent(web_search_tool, client=client, model="gpt-3.5-turbo")
    web_scraping_agent = ToolInterfaceAgent(web_scraping_tool, client=client, model="gpt-3.5-turbo")
    calculator_agent = ToolInterfaceAgent(calculator_tool, client=client, model="gpt-3.5-turbo")
    user_input_agent = ToolInterfaceAgent(user_input_tool, client=client, model="gpt-3.5-turbo")
    
    initial_message = "Hello! How can I assist you today?"
    
    agent = OrchestratorAgent(client=client, model="gpt-3.5-turbo", available_tools=[web_scraping_tool, web_search_agent, calculator_agent, user_input_tool], initial_message=initial_message)
    
    console.print(f'Agent: {initial_message}')

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chat...")
            break

        response = agent.run(user_input)
        console.print(f"Agent: {response.response.markdown}")