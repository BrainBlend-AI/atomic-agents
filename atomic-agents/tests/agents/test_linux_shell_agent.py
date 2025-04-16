import pytest
from unittest.mock import Mock, patch
import subprocess
import pathlib
from atomic_agents.agents.linux_shell_agent import (
    LinuxShellAgent,
    LinuxShellInputSchema,
    LinuxShellOutputSchema,
    LinuxCommandOutput,
    PathValidationError,
    LinuxCommandPipeline,
    CommandHistoryEntry
)
from atomic_agents.agents.base_agent import BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
import instructor


@pytest.fixture
def mock_instructor():
    mock = Mock(spec=instructor.Instructor)
    mock.chat.completions.create = Mock()
    return mock


@pytest.fixture
def shell_agent(mock_instructor):
    config = BaseAgentConfig(
        client=mock_instructor,
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator()
    )
    return LinuxShellAgent(config)


def test_initialization(shell_agent):
    """Test that the shell agent initializes with allowed commands"""
    assert len(shell_agent.allowed_commands) > 0
    assert 'ls' in shell_agent.allowed_commands
    assert shell_agent.command_help


def test_execute_allowed_command(shell_agent):
    """Test execution of an allowed command"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['ls'],
            returncode=0,
            stdout='file1.txt\nfile2.txt',
            stderr=''
        )

        result = shell_agent._execute_command('ls')

        assert result.command == 'ls'
        assert result.returncode == 0
        assert 'file1.txt' in result.stdout
        assert not result.stderr
        assert 'Successfully' in result.explanation


def test_execute_disallowed_command(shell_agent):
    """Test that disallowed commands are rejected"""
    result = shell_agent._execute_command('sudo rm -rf /')

    assert result.returncode != 0
    assert 'not allowed' in result.stderr
    assert 'not in the allowed list' in result.explanation


def test_execute_invalid_syntax(shell_agent):
    """Test handling of invalid command syntax"""
    result = shell_agent._execute_command('ls "unclosed quote')

    assert result.returncode != 0
    assert 'Invalid command syntax' in result.stderr


def test_command_with_working_directory(shell_agent):
    """Test command execution with working directory"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['pwd'],
            returncode=0,
            stdout='/test/dir',
            stderr=''
        )

        result = shell_agent._execute_command('pwd', working_dir='/test/dir')

        mock_run.assert_called_with(
            ['pwd'],
            capture_output=True,
            text=True,
            cwd='/test/dir'
        )
        assert result.stdout == '/test/dir'


def test_path_validation(shell_agent):
    """Test path validation logic"""
    with pytest.raises(PathValidationError):
        shell_agent._validate_path('/root/secret')

    with pytest.raises(PathValidationError):
        shell_agent._validate_path('.hidden')

    # Valid path should not raise
    test_path = pathlib.Path('/tmp/test')
    validated = shell_agent._validate_path(test_path)
    assert validated == test_path.resolve()


def test_command_pipeline(shell_agent):
    """Test command pipeline execution"""
    pipeline = LinuxCommandPipeline(
        commands=['ls', 'grep test']
    )

    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = ('test.txt', '')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = shell_agent._execute_pipeline(pipeline)

        assert result.command == 'ls | grep test'
        assert result.returncode == 0
        assert 'test.txt' in result.stdout


def test_command_history(shell_agent):
    """Test command history tracking"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['ls'],
            returncode=0,
            stdout='test.txt',
            stderr=''
        )

        shell_agent._execute_command('ls')

        history = shell_agent.get_command_history()
        assert len(history) == 1
        assert isinstance(history[0], CommandHistoryEntry)
        assert history[0].command == 'ls'
        assert history[0].success is True


def test_run_with_commands(shell_agent, mock_instructor):
    """Test full run with command extraction and execution"""
    mock_instructor.chat.completions.create.return_value = LinuxShellOutputSchema(
        chat_message="Let me help you with that. First, let's list the files: `ls -l`"
    )

    with patch.object(shell_agent, '_execute_command') as mock_execute:
        mock_execute.return_value = LinuxCommandOutput(
            command='ls -l',
            stdout='total 0\n-rw-r--r-- 1 user user 0 Jan 1 12:00 file.txt',
            stderr='',
            returncode=0,
            explanation='Successfully executed ls command'
        )

        result = shell_agent.run(LinuxShellInputSchema(
            instruction="List files in the current directory"
        ))

        assert isinstance(result, LinuxShellOutputSchema)
        assert len(result.command_outputs) == 1
        assert result.command_outputs[0].command == 'ls -l'
        assert 'file.txt' in result.command_outputs[0].stdout


def test_command_help_loading(shell_agent):
    """Test that command help is loaded from man pages"""
    assert shell_agent.command_help
    assert 'ls' in shell_agent.command_help
    assert 'synopsis' in shell_agent.command_help['ls']
    assert 'description' in shell_agent.command_help['ls']


def test_system_prompt_update(shell_agent):
    """Test that system prompt is updated with command information"""
    prompt = shell_agent.system_prompt_generator.generate_prompt()

    assert 'Linux command-line expert' in prompt
    assert 'Available commands:' in prompt
    for cmd in shell_agent.allowed_commands:
        assert cmd in prompt


def test_working_directory_validation(shell_agent):
    """Test working directory validation in input schema"""
    with pytest.raises(PathValidationError):
        LinuxShellInputSchema(
            instruction="list files",
            working_directory="/nonexistent/path"
        )


def test_pipeline_error_handling(shell_agent):
    """Test error handling in command pipelines"""
    pipeline = LinuxCommandPipeline(
        commands=['invalid', 'grep test']
    )

    result = shell_agent._execute_pipeline(pipeline)
    assert result.returncode != 0
    assert 'not allowed' in result.stderr


def test_command_history_limit(shell_agent):
    """Test command history with limit"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['ls'],
            returncode=0,
            stdout='',
            stderr=''
        )

        # Execute multiple commands
        for _ in range(5):
            shell_agent._execute_command('ls')

        # Get limited history
        history = shell_agent.get_command_history(limit=3)
        assert len(history) == 3