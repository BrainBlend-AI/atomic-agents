import os
from rich.console import Console
import instructor
from openai import OpenAI
from atomic_agents.agents.linux_shell_agent import LinuxShellAgent, LinuxShellInputSchema
from atomic_agents.agents.base_agent import BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Load environment variables and setup

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY."
    )

console = Console()

# Initialize the Linux Shell Agent
agent = LinuxShellAgent(
    config=BaseAgentConfig(
        client=instructor.from_openai(OpenAI(api_key=API_KEY)),
        model="gpt-4-turbo-preview",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a Linux command-line expert that helps users by:",
                "1. Understanding their natural language instructions",
                "2. Converting instructions into appropriate Linux commands",
                "3. Executing commands safely and explaining the results",
            ],
            steps=[
                "1. Analyze the user's request",
                "2. Choose appropriate Linux commands",
                "3. Execute commands safely",
                "4. Explain the results"
            ],
            output_instructions=[
                "Explain what commands you'll run and why",
                "Use only allowed commands",
                "Format commands exactly as they should be executed",
                "Explain command output in user-friendly terms"
            ]
        )
    )
)

# Chat loop
while True:
    # Get user input
    user_input = console.input("[bold green]You:[/bold green] ")
    if user_input.lower() in ["exit", "quit"]:
        break
    
    try:
        # Get response from agent
        response = agent.run(
            LinuxShellInputSchema(
                instruction=user_input
            )
        )
        
        # Display the chat message explaining what was done
        console.print("[bold blue]Assistant:[/bold blue]", response.chat_message)
        
        # Display command outputs
        for cmd_output in response.command_outputs:
            if cmd_output.stdout:
                console.print("\n[bold yellow]Command Output:[/bold yellow]")
                console.print(cmd_output.stdout)
            if cmd_output.stderr:
                console.print("\n[bold red]Errors:[/bold red]")
                console.print(cmd_output.stderr)
                
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

# View command history at the end
history = agent.get_command_history()
console.print("\n[bold purple]Command History:[/bold purple]")
for entry in history:
    status = "✓" if entry.success else "✗"
    console.print(f"{status} {entry.command} (in {entry.working_dir})")