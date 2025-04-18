import subprocess
import shlex
import os
import pathlib
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig


class CommandHistoryEntry(BaseModel):
    """Record of a command execution"""
    command: str = Field(..., description="The command that was executed")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the command was executed")
    working_dir: str = Field(..., description="Working directory when command was executed")
    success: bool = Field(..., description="Whether the command succeeded")


class PathValidationError(Exception):
    """Raised when a path validation fails"""
    pass


class LinuxCommandOutput(BaseModel):
    """Schema for Linux command execution output"""
    command: str = Field(..., description="The command that was executed")
    stdout: str = Field("", description="Standard output from command")
    stderr: str = Field("", description="Standard error from command")
    returncode: int = Field(0, description="Return code from command execution")
    explanation: str = Field("", description="Natural language explanation of the output")


class LinuxCommandPipeline(BaseModel):
    """Schema for a pipeline of Linux commands"""
    commands: List[str] = Field(..., description="List of commands to execute in sequence")
    pipe_operator: str = Field("|", description="The operator to use for piping commands")


class LinuxShellInputSchema(BaseIOSchema):
    """Schema for Linux shell command input"""
    instruction: str = Field(
        ..., 
        description="Natural language instruction describing the Linux operations to perform"
    )
    working_directory: Optional[str] = Field(
        None,
        description="Working directory for command execution. Defaults to current directory."
    )

    @field_validator('working_directory')
    @classmethod
    def validate_working_directory(cls, v):
        if v is not None:
            path = pathlib.Path(v)
            if not path.exists():
                raise PathValidationError(f"Working directory does not exist: {v}")
            if not path.is_dir():
                raise PathValidationError(f"Path is not a directory: {v}")
        return v


class LinuxShellOutputSchema(BaseIOSchema):
    """Schema for Linux shell command output"""
    chat_message: str = Field(
        ..., 
        description="Natural language response explaining what operations were performed"
    )
    command_outputs: List[LinuxCommandOutput] = Field(
        default_factory=list,
        description="Outputs from all executed commands"
    )


class LinuxShellAgent(BaseAgent):
    """Agent for executing Linux shell commands based on natural language instructions"""

    input_schema = LinuxShellInputSchema
    output_schema = LinuxShellOutputSchema

    def __init__(self, config: BaseAgentConfig):
        """Initialize the Linux shell agent with allowed commands and their documentation"""
        super().__init__(config)
        
        # Define allowed commands with descriptions
        self.allowed_commands = {
            'ls': 'List directory contents',
            'cp': 'Copy files and directories',
            'mv': 'Move (rename) files',
            'rm': 'Remove files or directories',
            'cat': 'Concatenate files and print on standard output',
            'more': 'File perusal filter for crt viewing',
            'less': 'Opposite of more',
            'pwd': 'Print name of current/working directory',
            'cd': 'Change the shell working directory',
            'mkdir': 'Make directories',
            'rmdir': 'Remove empty directories',
            'grep': 'Print lines that match patterns',
            'find': 'Search for files in a directory hierarchy',
            'head': 'Output the first part of files',
            'tail': 'Output the last part of files',
            'echo': 'Display a line of text',
            'sort': 'Sort lines of text files',
            'uniq': 'Report or omit repeated lines',
            'wc': 'Print newline, word, and byte counts',
            'cut': 'Remove sections from each line of files',
            'tr': 'Translate or delete characters',
            'sed': 'Stream editor for filtering and transforming text'
        }
        
        # Initialize command history
        self.command_history: List[CommandHistoryEntry] = []
        
        # Load detailed command help from man pages
        self._load_command_help()
        
        # Update system prompt with command information
        self._update_system_prompt()

    def _validate_path(self, path: Union[str, pathlib.Path]) -> pathlib.Path:
        """
        Validate a file system path.
        
        Args:
            path: Path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            PathValidationError: If path is invalid
        """
        try:
            path = pathlib.Path(path).resolve()
            
            # Check for common security issues
            if any(part.startswith('.') for part in path.parts):
                raise PathValidationError("Hidden directories/files not allowed")
                
            if str(path).startswith('/root'):
                raise PathValidationError("Root directory access not allowed")
                
            return path
            
        except Exception as e:
            raise PathValidationError(f"Invalid path: {str(e)}")

    def _execute_pipeline(self, pipeline: LinuxCommandPipeline, working_dir: Optional[str] = None) -> LinuxCommandOutput:
        """
        Execute a pipeline of commands.
        
        Args:
            pipeline: The pipeline of commands to execute
            working_dir: Optional working directory
            
        Returns:
            Output from the final command in the pipeline
        """
        processes = []
        
        try:
            # Start all processes in the pipeline
            for i, cmd in enumerate(pipeline.commands):
                tokens = shlex.split(cmd)
                
                # Validate first command in each pipe
                if tokens[0] not in self.allowed_commands:
                    return LinuxCommandOutput(
                        command=cmd,
                        stderr=f"Command '{tokens[0]}' not allowed",
                        returncode=1,
                        explanation="Command not in allowed list"
                    )
                
                stdin = processes[i - 1].stdout if i > 0 else None
                stdout = subprocess.PIPE if i < len(pipeline.commands) - 1 else subprocess.PIPE
                
                process = subprocess.Popen(
                    tokens,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir
                )
                processes.append(process)
            
            # Get output from last process
            stdout, stderr = processes[-1].communicate()
            returncode = processes[-1].returncode
            
            # Record in history
            self._record_command(
                " | ".join(pipeline.commands),
                working_dir or os.getcwd(),
                returncode == 0
            )
            
            return LinuxCommandOutput(
                command=" | ".join(pipeline.commands),
                stdout=stdout,
                stderr=stderr,
                returncode=returncode,
                explanation=f"Executed pipeline with {len(pipeline.commands)} commands"
            )
            
        finally:
            # Clean up processes
            for p in processes:
                try:
                    p.kill()
                except Exception:
                    pass

    def _record_command(self, command: str, working_dir: str, success: bool):
        """Record a command execution in history"""
        entry = CommandHistoryEntry(
            command=command,
            working_dir=working_dir,
            success=success
        )
        self.command_history.append(entry)

    def get_command_history(self, limit: Optional[int] = None) -> List[CommandHistoryEntry]:
        """Get the command execution history"""
        history = self.command_history
        if limit:
            history = history[-limit:]
        return history

    def _load_command_help(self):
        """Load man page summaries for allowed commands"""
        self.command_help = {}
        for cmd in self.allowed_commands.keys():
            try:
                result = subprocess.run(
                    ['man', cmd], 
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Extract the command synopsis and description
                    man_text = result.stdout
                    synopsis_start = man_text.find('SYNOPSIS')
                    description_start = man_text.find('DESCRIPTION')
                    if synopsis_start != -1 and description_start != -1:
                        synopsis = man_text[synopsis_start:description_start].split('\n')[1:3]
                        description = man_text[description_start:].split('\n')[1:3]
                        self.command_help[cmd] = {
                            'synopsis': ' '.join(synopsis).strip(),
                            'description': ' '.join(description).strip()
                        }
            except Exception as e:
                self.command_help[cmd] = {
                    'synopsis': f'Error loading help: {str(e)}',
                    'description': self.allowed_commands[cmd]
                }

    def _update_system_prompt(self):
        """Update system prompt with command information"""
        command_info = "\n".join([
            f"- {cmd}: {self.allowed_commands[cmd]}" 
            for cmd in sorted(self.allowed_commands.keys())
        ])
        
        self.system_prompt_generator.background = [
            "You are a Linux command-line expert that helps users by:",
            "1. Understanding their natural language instructions",
            "2. Converting instructions into appropriate Linux commands",
            "3. Executing commands safely and explaining the results",
            "\nAvailable commands:\n" + command_info
        ]

    def _execute_command(self, command: str, working_dir: Optional[str] = None) -> LinuxCommandOutput:
        """
        Safely execute a Linux command and capture its output.
        
        Args:
            command: The command string to execute
            working_dir: Optional working directory for command execution
            
        Returns:
            LinuxCommandOutput containing command results and explanation
        """
        # Check if command is a pipeline
        if '|' in command:
            pipeline = LinuxCommandPipeline(
                commands=[cmd.strip() for cmd in command.split('|')]
            )
            return self._execute_pipeline(pipeline, working_dir)
        
        # Split command into tokens for safety checking
        try:
            tokens = shlex.split(command)
        except Exception as e:
            return LinuxCommandOutput(
                command=command,
                stderr=f"Invalid command syntax: {str(e)}",
                returncode=1,
                explanation="The command syntax was invalid and could not be parsed."
            )

        # Safety check - only allow whitelisted commands
        if tokens[0] not in self.allowed_commands:
            return LinuxCommandOutput(
                command=command,
                stderr=f"Command '{tokens[0]}' not allowed. Allowed commands: {', '.join(sorted(self.allowed_commands.keys()))}",
                returncode=1,
                explanation="This command is not in the allowed list for safety reasons."
            )

        # Validate any file paths in the command
        try:
            for token in tokens[1:]:
                if not token.startswith('-'):
                    self._validate_path(token)
        except PathValidationError as e:
            return LinuxCommandOutput(
                command=command,
                stderr=f"Path validation error: {str(e)}",
                returncode=1,
                explanation=f"Invalid file path: {str(e)}"
            )

        try:
            # Execute command and capture output
            process = subprocess.run(
                tokens,
                capture_output=True,
                text=True,
                cwd=working_dir
            )
            
            # Record in history
            self._record_command(
                command,
                working_dir or os.getcwd(),
                process.returncode == 0
            )
            
            # Generate explanation based on command and output
            if process.returncode == 0:
                explanation = f"Successfully executed '{tokens[0]}' command."
            else:
                explanation = f"Command failed with error code {process.returncode}."
                
            return LinuxCommandOutput(
                command=command,
                stdout=process.stdout,
                stderr=process.stderr,
                returncode=process.returncode,
                explanation=explanation
            )
            
        except Exception as e:
            return LinuxCommandOutput(
                command=command,
                stderr=f"Error executing command: {str(e)}",
                returncode=1,
                explanation=f"An error occurred while trying to execute the command: {str(e)}"
            )

    def run(self, user_input: LinuxShellInputSchema) -> LinuxShellOutputSchema:
        """
        Process natural language instruction and execute appropriate Linux commands.

        Args:
            user_input: The natural language instruction and optional working directory

        Returns:
            LinuxShellOutputSchema containing results and explanation
        """
        # First let the base agent process the instruction
        base_response = super().run(user_input)
        
        # Extract commands to run from the response
        # This assumes the model's response includes commands in a structured way
        # Look for backtick-quoted commands
        import re
        commands_to_run = re.findall(r'`(.*?)`', base_response.chat_message)
        
        # Execute each command and collect outputs
        command_outputs = []
        for cmd in commands_to_run:
            output = self._execute_command(
                cmd, 
                working_dir=user_input.working_directory
            )
            command_outputs.append(output)
        
        return LinuxShellOutputSchema(
            chat_message=base_response.chat_message,
            command_outputs=command_outputs
        )