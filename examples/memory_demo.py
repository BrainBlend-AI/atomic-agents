from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from atomic_agents.lib.components.agent_memory import AgentMemory

console = Console()

def print_panel(title, content):
    console.print(Panel(content, title=title, expand=False, border_style="cyan"))

# Create a AgentMemory with a maximum of 5 messages
memory = AgentMemory(max_messages=5)

console.print("[bold magenta]AgentMemory Test Cases[/bold magenta]", justify="center")
console.print()

# Test Case 1: Adding regular messages and displaying the current history
content = Text()
memory.add_message("user", "Hello, how are you?")
memory.add_message("assistant", "I'm doing well, thank you for asking!")
memory.add_message("user", "Can you help me with the weather?")
content.append(f"Total messages: {memory.get_message_count()}\n\n")
content.append("Current history:\n")
for msg in memory.get_history():
    content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue'}")
print_panel("1. Adding regular messages", content)

# Test Case 2: Adding a message with a tool call and displaying the last message
content = Text()
tool_message = {
    "id": "weather_1",
    "type": "function",
    "function": {"name": "get_weather", "arguments": '{"location": "New York"}'}
}
memory.add_message("assistant", "Certainly! I'll check the weather for you.", tool_message=tool_message)
content.append(f"Total messages: {memory.get_message_count()}\n\n")
content.append("Last message:\n")
last_msg = memory.get_history()[-1]
content.append(f"- {last_msg.role}: {last_msg.content}\n", style="blue")
content.append(f"  Tool call: {last_msg.tool_calls}\n", style="yellow")
print_panel("2. Adding a message with a tool call", content)

# Test Case 3: Adding a tool response and displaying the last message
content = Text()
memory.add_message("tool", "The weather in New York is sunny with a high of 75°F.", tool_id="weather_1")
content.append(f"Total messages: {memory.get_message_count()}\n\n")
content.append("Last message:\n")
last_msg = memory.get_history()[-1]
content.append(f"- {last_msg.role}: {last_msg.content}\n", style="yellow")
content.append(f"  Tool call ID: {last_msg.tool_call_id}\n", style="yellow")
print_panel("3. Adding a tool response", content)

# Test Case 4: Testing overflow management by adding more messages than the maximum allowed
content = Text()
memory.add_message("user", "Thanks for the weather info!")
content.append(f"Total messages: {memory.get_message_count()}\n\n")
content.append("Current history (should only have 5 most recent messages):\n")
for msg in memory.get_history():
    content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue' if msg.role == 'assistant' else 'yellow'}")
print_panel("4. Testing overflow management", content)

# Test Case 5: Testing dump and load functionality
content = Text()
dumped_data = memory.dump()
content.append("Dumped data:\n")
content.append(str(dumped_data), style="dim")
content.append("\n\n")
new_memory = AgentMemory(max_messages=5)
new_memory.load(dumped_data)
content.append("Loaded memory:\n")
for msg in new_memory.get_history():
    content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue' if msg.role == 'assistant' else 'yellow'}")
content.append(f"\nTotal messages in loaded memory: {new_memory.get_message_count()}")
print_panel("5. Testing dump and load", content)

# Test Case 6: Testing copy functionality
content = Text()
copied_memory = memory.copy()
content.append(f"Original memory message count: {memory.get_message_count()}\n")
content.append(f"Copied memory message count: {copied_memory.get_message_count()}\n\n")
content.append("Adding a message to the copy:\n")
copied_memory.add_message("user", "This is a new message in the copy.")
content.append(f"Original memory message count: {memory.get_message_count()}\n")
content.append(f"Copied memory message count: {copied_memory.get_message_count()}")
print_panel("6. Testing copy", content)

# Test Case 7: Testing loading a larger buffer than max_messages
content = Text()
large_buffer = [
    {"role": "user", "content": f"Message {i}"} for i in range(10)
]
large_memory = AgentMemory(max_messages=5)
large_memory.load(large_buffer)
content.append(f"Total messages after loading large buffer: {large_memory.get_message_count()}\n\n")
content.append("Current history (should only have 5 most recent messages):\n")
for msg in large_memory.get_history():
    content.append(f"- {msg.role}: {msg.content}\n", style="green")
print_panel("7. Testing loading a larger buffer than max_messages", content)

# Test Case 8: Testing adding messages with different content types
content = Text()
mixed_memory = AgentMemory(max_messages=10)
mixed_memory.add_message("user", "Hello")
mixed_memory.add_message("assistant", {"text": "Hi there!", "confidence": 0.95})
mixed_memory.add_message("system", {"command": "reset_conversation"})
content.append(f"Total messages in mixed memory: {mixed_memory.get_message_count()}\n\n")
content.append("Mixed memory contents:\n")
for msg in mixed_memory.get_history():
    content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue' if msg.role == 'assistant' else 'red'}")
print_panel("8. Testing adding messages with different content types", content)