# Browser.AI Copilot Instructions

## Project Overview

Browser.AI is a sophisticated browser automation framework that makes websites accessible to AI agents through a modular architecture with four core components: Agent, Controller, Browser, and DOM services.

## Core Architecture Patterns

### Agent-Centric Design
- **Entry Point**: Always start with `Agent` class in `browser_ai/agent/service.py`
- **Required Parameters**: `task` (string), `llm` (BaseChatModel from langchain)
- **Key Pattern**: `Agent(task="...", llm=model)` then `await agent.run()`

### Component Initialization Order
```python
# Standard pattern from examples/simple.py
llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
agent = Agent(task=task, llm=llm)
await agent.run()
```

### Registry-Based Action System
- **Location**: `browser_ai/controller/registry/service.py`
- **Pattern**: Actions registered via `@registry.action(description, param_model)` decorator
- **Exclusion**: Use `Controller(exclude_actions=['action_name'])` to remove default actions
- **Custom Output**: Use `Controller(output_model=YourPydanticModel)` for structured results

## Critical Development Workflows

### Running Examples
- **Simple**: `python examples/simple.py` (requires OPENAI_API_KEY in .env)
- **GUI Launch**: `python launch.py` (auto-installs GUI dependencies)
- **Web Interface**: `python -m browser_ai_gui.main web --port 5000`
- **Desktop GUI**: `python -m browser_ai_gui.main tkinter`

### Testing Patterns
- **Web Test**: `python test_web.py` (tests GUI on port 5001)
- **Dependencies**: Install GUI deps via `pip install ".[gui]"` or use launch.py

### Project Structure Navigation
- **Core**: `browser_ai/` - Main framework code
- **GUI**: `browser_ai_gui/` - Web and Tkinter interfaces  
- **Examples**: `examples/` - Usage patterns organized by type
- **Docs**: `docs/` - Technical specifications with mermaid diagrams

## Browser.AI Specific Conventions

### LLM Integration Patterns
- **Multi-Model Support**: Agent supports different LLMs per component (`llm` for actions, `planner_llm` for planning)
- **Vision Toggle**: `use_vision=True` (default) enables screenshot analysis
- **Message Management**: Uses `MessageManager` for token-aware conversation handling

### Browser Configuration
```python
# From browser_ai/browser/browser.py
browser_config = BrowserConfig(
    headless=False,              # Default: False (visible browser)
    disable_security=True,       # Default: True (bypass CSP/CORS)
    extra_chromium_args=[]       # Custom browser flags
)
```

### DOM Processing Specifics
- **Element Detection**: Uses JavaScript injection via `buildDomTree.js`
- **Highlighting**: Visual element highlighting for AI agent vision
- **Coordinate System**: Custom coordinate mapping in `dom/history_tree_processor/`
- **Viewport Handling**: Automatic viewport expansion and scrolling

### Action Result Pattern
```python
# Standard action return from controller/service.py
return ActionResult(
    is_done=True,                    # Task completion flag
    extracted_content=data,          # String or JSON result
    include_in_memory=True          # Whether to remember this step
)
```

### Async Execution Model
- **All Operations**: Use `async`/`await` throughout
- **Browser Management**: Automatic browser lifecycle management
- **Resource Cleanup**: Built-in garbage collection patterns

## Integration Points

### Custom Action Registration
```python
# Pattern from controller/registry/service.py
@controller.registry.action("Description", param_model=YourModel)
async def custom_action(params: YourModel):
    # Your implementation
    return ActionResult(...)
```

### Configuration Management
- **GUI Config**: Uses `browser_ai_gui/config.py` ConfigManager
- **Environment**: Load via `python-dotenv` (.env files)
- **Paths**: Use `available_file_paths` parameter for file access restrictions

### Error Handling Specifics
- **Retry Logic**: Built-in retry with `max_failures=3`, `retry_delay=10`
- **Rate Limits**: Handles OpenAI/Anthropic rate limiting automatically
- **Browser Recovery**: Automatic browser restart on crashes

## Key Files for AI Understanding

- `browser_ai/agent/service.py` - Main orchestration logic and Agent class
- `browser_ai/controller/service.py` - Action execution and registry management
- `browser_ai/browser/browser.py` - Enhanced Playwright wrapper with config
- `examples/features/` - Real-world usage patterns and advanced features
- `launch.py` - Smart dependency management and launcher patterns
- `browser_ai_gui/main.py` - GUI application entry points and argument parsing

## Memory and Performance Notes

- **Token Management**: Automatic message trimming via `max_input_tokens=128000`
- **Image Processing**: Screenshot analysis with `image_tokens=800` estimation  
- **DOM Caching**: XPath caching in `DomService` for performance
- **Garbage Collection**: Explicit GC calls in browser operations
- **History Tracking**: Configurable conversation saving via `save_conversation_path`