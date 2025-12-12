# Using the Agent in Browser.AI

## Overview

The `Agent` class is the primary entry point for automating browser interactions in Browser.AI. It orchestrates tasks by leveraging a large language model (LLM) to plan and execute actions on web pages. This guide walks you through setting up and using the Agent effectively.

## Prerequisites

- Python 3.8 or higher
- Required dependencies: Install via `pip install browser-ai` or from the project root with `uv sync`
- An LLM provider (e.g., OpenAI API key for GPT models)
- Environment variables: Set `OPENAI_API_KEY` in a `.env` file or your environment

## Basic Usage

### 1. Import the Agent

```python
from browser_ai.agent.service import Agent
from langchain_openai import ChatOpenAI
```

### 2. Initialize the LLM

```python
llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
```

### 3. Create and Run the Agent

```python
agent = Agent(task="Navigate to example.com and extract the main heading", llm=llm)
result = await agent.run()
print(result)
```

### Complete Example

See `examples/simple.py` for a runnable example:

```python
import asyncio
from browser_ai.agent.service import Agent
from langchain_openai import ChatOpenAI

async def main():
    llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
    agent = Agent(task="Go to https://example.com and get the title of the page", llm=llm)
    result = await agent.run()
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

Run it with: `python examples/simple.py`

## Advanced Configuration

### Custom Browser Settings

```python
from browser_ai.browser.browser import BrowserConfig

browser_config = BrowserConfig(
    headless=False,              # Run browser in visible mode
    disable_security=True,       # Bypass CSP/CORS for testing
    extra_chromium_args=["--no-sandbox"]
)

agent = Agent(
    task="Your task here",
    llm=llm,
    browser_config=browser_config
)
```

### Vision and Memory Options

```python
agent = Agent(
    task="Analyze this webpage visually",
    llm=llm,
    use_vision=True,              # Enable screenshot analysis (default: True)
    max_input_tokens=128000,      # Token limit for conversation
    save_conversation_path="conversation.json"  # Save chat history
)
```

### Multiple LLMs

```python
agent = Agent(
    task="Complex task",
    llm=llm,                      # For action execution
    planner_llm=ChatOpenAI(model='gpt-4o-mini')  # For planning (optional)
)
```

## Controller Customization

### Excluding Actions

```python
from browser_ai.controller.service import Controller

controller = Controller(exclude_actions=['click_element', 'type_text'])
agent = Agent(task="Task without clicking or typing", llm=llm, controller=controller)
```

### Custom Output Model

```python
from pydantic import BaseModel

class CustomResult(BaseModel):
    title: str
    links: list[str]

controller = Controller(output_model=CustomResult)
agent = Agent(task="Extract title and links", llm=llm, controller=controller)
```

## Error Handling and Retries

The Agent includes built-in retry logic:

```python
agent = Agent(
    task="Reliable task",
    llm=llm,
    max_failures=3,               # Max retry attempts
    retry_delay=10                # Delay between retries in seconds
)
```

## Integration with GUI

For GUI-based usage:

- **Web Interface**: Run `python -m browser_ai_gui.main web --port 5000`
- **Desktop GUI**: Run `python -m browser_ai_gui.main tkinter`
- **Launcher**: Use `python launch.py` for auto-dependency installation

## Troubleshooting

### Common Issues

1. **Browser Not Starting**: Ensure Playwright is installed (`playwright install`)
2. **LLM Errors**: Check API keys and rate limits
3. **Element Not Found**: Tasks may need more specific instructions
4. **Performance**: Reduce `max_input_tokens` or disable vision for faster execution

### Debugging

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check browser logs and conversation history for insights.

## Examples Directory

Explore `examples/` for more patterns:

- `examples/simple.py`: Basic usage
- `examples/features/`: Advanced features
- `examples/use-cases/`: Real-world scenarios

## API Reference

For detailed API docs, see:

- [Agent Implementation](agent-implementation.md)
- [Controller Actions](controller-actions.md)
- [Browser Management](browser-management.md)

## Contributing

When extending the Agent, follow the registry pattern for custom actions. See `browser_ai/controller/registry/service.py` for details.