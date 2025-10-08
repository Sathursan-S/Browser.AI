# Browser.AI Chat Interface GUI

A beautiful, real-time chat interface for monitoring Browser.AI automation tasks. This GUI displays logs, current steps, and outputs in a user-friendly format alongside your Playwright browser automation.

## Features

- 🎯 **Real-time Progress Tracking** - See automation steps as they happen
- 📊 **Formatted Logs** - Beautifully formatted messages with timestamps and icons
- 🔍 **Action Monitoring** - View each action (clicks, typing, navigation) in detail
- ✅ **Result Display** - See extracted content, errors, and success messages
- 🌐 **Browser State Updates** - Track URL changes, page titles, and element counts
- 📈 **Task Completion Tracking** - Monitor overall progress and final results
- 🎨 **Modern UI** - Clean, responsive design with status panels and controls

## Quick Start

### Option 1: Automated Run (Easiest)
```python
import asyncio
from langchain_openai import ChatOpenAI  # or your preferred LLM
from browser_ai import run_agent_with_gui

# This creates the agent, launches the GUI, and runs automation
async def main():
    llm = ChatOpenAI(model="gpt-4")  # Configure your LLM
    
    history = await run_agent_with_gui(
        task="Navigate to example.com and extract the main heading",
        llm=llm,
        max_steps=10,
        gui_port=7860,  # GUI will be available at http://localhost:7860
        gui_title="My Automation Task"
    )
    
    print(f"✅ Completed {len(history.history)} steps")

asyncio.run(main())
```

### Option 2: Manual Control
```python
import asyncio
from langchain_openai import ChatOpenAI
from browser_ai import create_agent_with_gui

async def main():
    llm = ChatOpenAI(model="gpt-4")
    
    # Create agent with integrated GUI
    agent, chat_gui = create_agent_with_gui(
        task="Your automation task here",
        llm=llm,
        gui_port=7860
    )
    
    # Run the automation (GUI updates automatically)
    history = await agent.run(max_steps=10)
    
    # GUI remains active for monitoring
    print("🌐 Check http://localhost:7860 for detailed logs")

asyncio.run(main())
```

### Option 3: Custom Integration
```python
from browser_ai import Agent, BrowserAIChat

# Create the chat interface
chat_gui = BrowserAIChat(
    title="Custom Automation Chat",
    port=7860
)

# Create agent with GUI callbacks
agent = Agent(
    task="Your task",
    llm=your_llm,
    register_new_step_callback=chat_gui.step_callback,
    register_done_callback=chat_gui.done_callback
)

# Launch GUI
chat_gui.launch()

# Set task and run
chat_gui.set_task("Your automation task")
history = await agent.run(max_steps=10)
```

## GUI Interface

When you run any of the above examples, open **http://localhost:7860** in your browser to see:

### Main Chat Area
- Real-time log messages with timestamps
- Step-by-step automation progress  
- Action results and extracted content
- Error messages and debugging info
- Task completion notifications

### Status Panel
- Current task description
- Current automation step number
- Running/Idle status indicator
- Last update timestamp

### Control Panel  
- Current task display
- Step counter
- Clear chat button
- Auto-refresh toggle
- Manual refresh button

## Message Types

The GUI displays different types of messages with unique formatting:

| Icon | Type | Description |
|------|------|-------------|
| 🚀 | Task Started | New automation task beginning |
| 🎯 | Step Info | Current step goal and planned actions |
| ✅ | Success | Successful action completion |
| ❌ | Error | Action errors and failures |
| 📄 | Content | Extracted content and data |
| ⚠️ | Warning | Warnings and status updates |
| 🌐 | Page Update | Browser navigation and page changes |
| 🏁 | Completion | Task finished successfully |

## Demo and Testing

### Run Interactive Demo
```bash
cd browser_ai/gui
python demo.py
```

Choose from:
1. **Automated simulation** - Realistic browser automation sequence
2. **Interactive mode** - Control the demo manually  
3. **GUI only** - Just launch the interface

### Run Tests
```bash
python test_simple_gui.py  # Standalone GUI tests
python test_chat_gui.py    # Full integration tests
```

## Configuration Options

### BrowserAIChat Options
```python
chat_gui = BrowserAIChat(
    title="Custom Title",           # GUI window title
    port=7860                      # Port for web interface
)
```

### Integration Options
```python
agent, chat_gui = create_agent_with_gui(
    task="Your task",
    llm=your_llm,
    gui_port=7860,                 # GUI port
    gui_title="Custom Title",      # GUI title
    # All other Agent parameters supported:
    max_failures=3,
    use_vision=True,
    generate_gif=True,
    # ... etc
)
```

## Advanced Usage

### Custom Callbacks
```python
def custom_step_callback(state, output, step_num):
    print(f"Step {step_num}: {output.current_state.next_goal}")
    # Your custom logic here
    
    # Still call the GUI callback
    chat_gui.step_callback(state, output, step_num)

agent = Agent(
    task="Your task",
    llm=llm,
    register_new_step_callback=custom_step_callback,
    register_done_callback=chat_gui.done_callback
)
```

### Manual Updates
```python
# Add custom messages
chat_gui.add_message("🔧 Setup", "Initializing custom workflow")

# Add step information  
chat_gui.add_step_info(1, "Custom step goal", [])

# Add results
chat_gui.add_result("success", "Custom operation completed")

# Update browser state
chat_gui.add_browser_state(browser_state)
```

## Best Practices

1. **Port Management** - Use different ports for multiple concurrent automations
2. **Task Descriptions** - Provide clear, descriptive task names
3. **Error Handling** - The GUI automatically displays errors and debugging info
4. **Resource Management** - GUI stays active after automation completes for log review
5. **Integration** - Use existing Agent callbacks for seamless integration

## Troubleshooting

### Common Issues

**GUI not loading?**
- Check that the port (default 7860) isn't in use
- Try a different port: `gui_port=7861`
- Ensure gradio is installed: `pip install gradio`

**Messages not updating?**  
- Ensure you're using the callback integration methods
- Check that `register_new_step_callback` is set correctly
- Try manual refresh in the GUI

**Import errors?**
- Install dependencies: `pip install gradio python-dotenv`
- Ensure browser_ai package is properly installed

## Examples

See the `/browser_ai/gui/` directory for complete examples:
- `example.py` - Usage instructions and code examples
- `demo.py` - Interactive demo with realistic simulation
- `test_simple_gui.py` - Standalone functionality test

## Integration with Existing Code

The GUI integrates seamlessly with existing Browser.AI code:

```python
# Before (existing code)
agent = Agent(task="Your task", llm=llm)
history = await agent.run()

# After (with GUI) 
agent, chat_gui = create_agent_with_gui(task="Your task", llm=llm)
history = await agent.run()
# GUI automatically shows all progress at http://localhost:7860
```

No changes to existing automation logic required! 🎉