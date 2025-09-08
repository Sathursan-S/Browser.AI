# Reactive Agents for Browser.AI

This module provides reactive agent implementations that extend Browser.AI's capabilities with event-driven architecture, multi-agent collaboration, and advanced workflow management using LangGraph and CrewAI.

## Overview

The reactive agents build upon the existing Browser.AI Agent class while adding:

- **Event-driven execution**: React to browser state changes and user interactions
- **Advanced workflow management**: Complex conditional logic and parallel execution
- **Multi-agent collaboration**: Specialized agents working together
- **Enhanced error recovery**: Context-aware error handling and recovery
- **Real-time monitoring**: Event streams and performance metrics

## Agent Types

### 1. BaseReactiveAgent

The foundation class that adds reactive capabilities to the standard Browser.AI Agent:

```python
from browser_ai.agent.reactive import BaseReactiveAgent

class MyReactiveAgent(BaseReactiveAgent):
    async def reactive_step(self, step_info=None):
        # Implement your reactive logic here
        pass
    
    async def get_recovery_action(self, error, context):
        # Define recovery strategies
        return "retry"
    
    async def execute_recovery_action(self, action, error, context):
        # Execute recovery actions
        await asyncio.sleep(1.0)
```

**Key Features:**
- Event emission and subscription
- Automatic error recovery
- Performance metrics tracking
- State change notifications
- Asynchronous event processing

### 2. LangGraphReactiveAgent

Uses LangGraph for workflow management with state machines and conditional logic:

```python
from browser_ai.agent.reactive import LangGraphReactiveAgent

agent = LangGraphReactiveAgent(
    task="Extract product information from e-commerce sites",
    llm=your_llm,
    enable_parallel_execution=True,
    enable_conditional_flow=True,
    max_parallel_actions=3
)
```

**Key Features:**
- State graph workflow execution
- Conditional branching based on browser state
- Parallel action execution
- Complex workflow patterns
- Visual workflow debugging

**Workflow Nodes:**
- `analyze_state`: Analyze current browser state
- `plan_actions`: Plan actions based on analysis
- `execute_actions`: Execute planned actions
- `parallel_executor`: Execute actions in parallel
- `evaluate_results`: Evaluate action results
- `handle_errors`: Handle errors with recovery strategies
- `process_events`: Process reactive events

### 3. CrewAIReactiveAgent

Uses CrewAI for multi-agent collaboration with specialized roles:

```python
from browser_ai.agent.reactive import CrewAIReactiveAgent

agent = CrewAIReactiveAgent(
    task="Research competitor pricing and generate report",
    llm=your_llm,
    max_concurrent_agents=3,
    cooperation_mode="collaborative"
)
```

**Key Features:**
- Multi-agent collaboration
- Specialized agent roles
- Task delegation and coordination
- Cross-agent communication
- Hierarchical or collaborative modes

**Default Agent Roles:**
- **Navigator**: Handles page navigation and transitions
- **Extractor**: Specializes in content extraction and analysis
- **Interactor**: Manages element interactions and form filling
- **Analyzer**: Coordinates tasks and monitors progress

## Installation

The reactive agents are included with Browser.AI. Ensure you have the required dependencies:

```bash
# LangGraph support
pip install langgraph>=0.5.4

# CrewAI support  
pip install crewai>=0.177.0

# Optional: Enhanced LLM providers
pip install langchain-openai langchain-anthropic
```

## Quick Start

### Basic Reactive Agent

```python
import asyncio
from langchain_openai import ChatOpenAI
from browser_ai.agent.reactive import LangGraphReactiveAgent

async def main():
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # Create reactive agent
    agent = LangGraphReactiveAgent(
        task="Go to https://example.com and extract the main heading",
        llm=llm
    )
    
    # Subscribe to events
    agent.subscribe_to_event("langgraph", 
        lambda event: print(f"Event: {event.event_type}"))
    
    # Run the agent
    history = await agent.run(max_steps=5)
    
    print(f"Task completed: {history.is_done()}")
    print(f"Result: {history.final_result()}")

asyncio.run(main())
```

### Multi-Agent Collaboration

```python
from browser_ai.agent.reactive import CrewAIReactiveAgent

async def collaborative_task():
    agent = CrewAIReactiveAgent(
        task="Research the top 3 Python frameworks and create a comparison",
        llm=ChatOpenAI(model="gpt-4"),
        cooperation_mode="collaborative"
    )
    
    # Run with crew collaboration
    history = await agent.run(max_steps=10)
    
    # Get crew status
    status = agent.get_crew_status()
    print(f"Agents involved: {status['agent_roles']}")
    
    return history
```

## Advanced Features

### Event System

The reactive agents emit and respond to various events:

```python
# Subscribe to specific events
agent.subscribe_to_event("browser_state_changed", handle_navigation)
agent.subscribe_to_event("action_completed", handle_action_result)
agent.subscribe_to_event("error_occurred", handle_errors)

# Emit custom events
await agent.emit_event("custom", "user_action", {"action": "pause"})

# Handle all events
agent.subscribe_to_event("*", handle_all_events)
```

### Error Recovery

Configure intelligent error recovery:

```python
agent = LangGraphReactiveAgent(
    task="Your task",
    llm=llm,
    auto_recovery=True,
    recovery_strategies=['retry', 'alternative_path', 'human_intervention']
)

# Custom recovery logic
async def custom_recovery(self, error, context):
    if "timeout" in str(error).lower():
        return "wait_and_retry"
    elif "element_not_found" in str(error).lower():
        return "refresh_and_retry"
    return "escalate"
```

### Performance Monitoring

Track performance and metrics:

```python
# Get real-time metrics
metrics = agent.get_metrics()
print(f"Events processed: {metrics['events_processed']}")
print(f"Recovery actions: {metrics['recovery_actions']}")
print(f"Average response time: {metrics['avg_response_time']}")

# Workflow status (LangGraph)
status = agent.get_workflow_status()
print(f"Current goal: {status['current_goal']}")
print(f"Actions queued: {status['actions_queued']}")

# Crew status (CrewAI)
crew_status = agent.get_crew_status()
print(f"Active agents: {crew_status['active_agents']}")
print(f"Pending tasks: {crew_status['pending_tasks']}")
```

## Use Cases

### 1. Complex Web Scraping

```python
# LangGraph for structured scraping with conditional logic
agent = LangGraphReactiveAgent(
    task="Scrape product data with pagination and filtering",
    llm=llm,
    enable_conditional_flow=True
)
```

### 2. Multi-Step Workflows

```python
# CrewAI for complex workflows requiring different skills
agent = CrewAIReactiveAgent(
    task="Research competitors, analyze pricing, and generate report",
    llm=llm,
    cooperation_mode="hierarchical"
)
```

### 3. Monitoring and Alerting

```python
# Reactive monitoring with event-driven responses
agent = LangGraphReactiveAgent(
    task="Monitor website for changes and send alerts",
    llm=llm,
    enable_event_system=True
)

agent.subscribe_to_event("content_changed", send_alert)
```

### 4. Form Automation

```python
# Multi-agent form filling with validation
agent = CrewAIReactiveAgent(
    task="Fill complex multi-step application form",
    llm=llm,
    agent_roles=[navigator_role, form_filler_role, validator_role]
)
```

## Context7 Integration

The reactive agents support Context7 patterns for enhanced contextual awareness:

```python
# Context-aware execution
agent = LangGraphReactiveAgent(
    task="Your task",
    llm=llm,
    context7_config={
        'dimensions': ['temporal', 'semantic', 'user'],
        'analysis_depth': 'deep'
    }
)
```

See [Context7 Integration Guide](context7_integration.md) for detailed information.

## Examples

Check out the [examples directory](examples/) for comprehensive usage examples:

- `basic_usage.py`: Getting started with reactive agents
- `advanced_workflows.py`: Complex workflow patterns  
- `error_handling.py`: Advanced error recovery
- `monitoring.py`: Real-time monitoring and alerting
- `multi_agent.py`: Multi-agent collaboration patterns

## Configuration

### LangGraph Configuration

```python
LangGraphReactiveAgent(
    task="Your task",
    llm=llm,
    # Workflow configuration
    enable_parallel_execution=True,
    max_parallel_actions=3,
    enable_conditional_flow=True,
    
    # Recovery configuration
    recovery_strategies=['retry', 'alternative_path'],
    
    # Event system
    enable_event_system=True,
    event_buffer_size=1000,
    auto_recovery=True
)
```

### CrewAI Configuration

```python
CrewAIReactiveAgent(
    task="Your task", 
    llm=llm,
    # Crew configuration
    max_concurrent_agents=3,
    cooperation_mode="collaborative",  # or "hierarchical"
    enable_agent_memory=True,
    
    # Custom agent roles
    agent_roles=custom_roles,
    
    # Event system
    enable_event_system=True
)
```

## Best Practices

### 1. Event Management
- Subscribe to relevant events only
- Use appropriate event priorities
- Handle events asynchronously when possible
- Clean up event subscriptions

### 2. Error Handling
- Define specific recovery strategies for common errors
- Use context-aware error recovery
- Set appropriate timeout values
- Log recovery attempts for analysis

### 3. Performance
- Monitor metrics regularly
- Tune parallel execution limits
- Optimize workflow patterns
- Use event filtering to reduce noise

### 4. Multi-Agent Coordination
- Define clear agent roles and responsibilities
- Use appropriate cooperation modes
- Share context efficiently between agents
- Monitor agent performance individually

## Troubleshooting

### Common Issues

1. **Event System Not Starting**
   ```python
   # Ensure reactive system is started
   await agent.start_reactive_system()
   ```

2. **Recovery Actions Failing**
   ```python
   # Check recovery strategy configuration
   agent.recovery_strategies = ['retry', 'refresh', 'escalate']
   ```

3. **Performance Issues**
   ```python
   # Adjust buffer sizes and limits
   agent.event_buffer_size = 500  # Reduce if memory is constrained
   agent.max_parallel_actions = 2  # Reduce if system is overloaded
   ```

4. **CrewAI Import Errors**
   ```bash
   pip install crewai>=0.177.0
   ```

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed event processing and workflow execution
```

## Contributing

To contribute to the reactive agents:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

See the main Browser.AI contributing guidelines for more details.

## License

This module is part of Browser.AI and follows the same license terms.