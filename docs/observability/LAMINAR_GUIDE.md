# Laminar Observability for Browser.AI

Complete observability implementation using [Laminar](https://www.lmnr.ai/) for the Browser.AI agent system.

## Features

✅ **Comprehensive Tracing**
- Agent execution traces with step-by-step breakdown
- Browser operation monitoring
- LLM call tracking with token usage
- Action execution with parameters and results

✅ **Prompt Management**
- Centralized prompt registry with versioning
- A/B testing support for prompt optimization
- Rollback capabilities
- Template variable validation

✅ **Evaluation Framework**
- Task success evaluation
- Action accuracy metrics
- Latency and performance analysis
- Comprehensive multi-evaluator support

✅ **Metrics Collection**
- Real-time session tracking
- Aggregated statistics
- Action breakdown analysis
- Performance profiling

## Setup

### 1. Install Laminar

```bash
pip install lmnr
```

### 2. Set up Laminar API Key

Get your API key from [Laminar Dashboard](https://www.lmnr.ai/) and set it:

```bash
export LMNR_PROJECT_API_KEY="your-api-key-here"
```

Or add to your `.env` file:

```
LMNR_PROJECT_API_KEY=your-api-key-here
```

### 3. Initialize Laminar (Optional)

If you want to customize the Laminar configuration:

```python
from lmnr import Laminar

# Initialize with custom settings
Laminar.initialize(
    project_api_key="your-api-key",
    # Additional configuration
)
```

## Usage

### Basic Agent Execution with Tracing

```python
import asyncio
from langchain_openai import ChatOpenAI
from browser_ai import Agent
from browser_ai.observability import metrics_collector

# Create LLM
llm = ChatOpenAI(model='gpt-4o', temperature=0.0)

# Create agent with task
agent = Agent(
    task="Search for the latest AI news",
    llm=llm,
)

# Start metrics collection
session_id = "session-001"
metrics_collector.start_session(
    task=agent.task,
    session_id=session_id,
)

# Run agent - automatic tracing enabled
history = await agent.run()

# Complete metrics collection
final_metrics = metrics_collector.complete_session(
    session_id=session_id,
    successful=history.is_done(),
)

print(f"Task completed in {final_metrics.total_steps} steps")
print(f"Total actions: {final_metrics.total_actions}")
```

### Using Prompt Manager

```python
from browser_ai.observability import PromptManager, PromptType

# Get global prompt manager
pm = PromptManager()

# Register a new prompt version
pm.register_prompt(
    prompt_id="custom_system",
    version="2.0.0",
    prompt_type=PromptType.SYSTEM,
    template="""You are an advanced AI agent.
Task: {task}
Context: {context}
Available tools: {tools}""",
    variables=["task", "context", "tools"],
    metadata={"author": "Your Name", "description": "Enhanced system prompt"},
)

# Render the prompt
rendered = pm.render_prompt(
    prompt_id="custom_system",
    version="2.0.0",
    task="Book a flight",
    context="User wants to travel next week",
    tools="search, click, input_text",
)

# Export prompts for backup
pm.export_prompts("prompts_backup.json")

# Import prompts
pm.import_prompts("prompts_backup.json")
```

### Running Evaluations

```python
from browser_ai.observability import (
    TaskSuccessEvaluator,
    ActionAccuracyEvaluator,
    ComprehensiveEvaluator,
)

# Run single evaluator
success_eval = TaskSuccessEvaluator()
result = await success_eval.evaluate(
    task="Search for Python tutorials",
    history=agent.history,
    expected_result="Python tutorials found",
)

print(f"Success Score: {result.score}")
print(f"Passed: {result.passed}")
print(f"Metadata: {result.metadata}")

# Run comprehensive evaluation
comprehensive = ComprehensiveEvaluator()
all_results = await comprehensive.evaluate_all(
    task="Search for Python tutorials",
    history=agent.history,
)

summary = comprehensive.get_summary(all_results)
print(f"Overall Score: {summary['overall_score']}")
print(f"All Passed: {summary['all_passed']}")
```

### Viewing Metrics

```python
from browser_ai.observability import metrics_collector

# Get aggregated statistics
stats = metrics_collector.get_aggregated_stats()

print(f"Total Sessions: {stats['total_sessions']}")
print(f"Success Rate: {stats['success_rate']:.2%}")
print(f"Avg Duration: {stats['avg_duration_seconds']:.2f}s")
print(f"Most Used Actions: {stats['most_used_actions']}")

# Export metrics
metrics_collector.export_metrics("metrics_report.json")
```

## Viewing Traces in Laminar

### 1. Access Laminar Dashboard

Navigate to https://www.lmnr.ai/ and log in to your account.

### 2. View Traces

All agent executions are automatically traced and visible in the Laminar dashboard:

- **Traces Tab**: See complete execution traces with timing
- **Spans**: Drill down into individual operations
- **Metrics**: View custom metrics and events
- **Prompts**: Track prompt usage and versions

### 3. Key Trace Components

**Agent Level**:
- `agent.task_execution`: Complete task execution workflow
- `agent.run`: Main run loop
- `agent.step.{N}`: Individual step execution

**Step Level**:
- `agent.get_state`: Browser state capture
- `agent.planner`: Strategic planning (if enabled)
- `agent.llm_call`: LLM invocation with parameters
- `controller.multi_act`: Action execution batch

**Action Level**:
- Individual actions with parameters and results
- Browser operations (navigation, clicking, typing)
- Content extraction

**Browser Level**:
- `browser.init`: Browser initialization
- `browser.get_state_details`: State capture with metadata

## Custom Instrumentation

### Adding Custom Traces

```python
from lmnr import Laminar, observe

@observe(name="custom_operation")
async def my_custom_function(param1, param2):
    with Laminar.start_as_current_span(
        name="custom.detailed_step",
        input={"param1": param1, "param2": param2},
        span_type="DEFAULT",
    ):
        result = await some_operation(param1, param2)
        
        Laminar.set_span_output({"result": result})
        
        return result
```

### Recording Custom Events

```python
from lmnr import Laminar

# Record custom metrics
Laminar.event(
    name="custom_metric",
    value={
        "metric_name": "user_satisfaction",
        "value": 0.95,
        "timestamp": datetime.now().isoformat(),
    },
)
```

### Custom Evaluator

```python
from browser_ai.observability import AgentEvaluator, EvaluationResult

class CustomEvaluator(AgentEvaluator):
    def __init__(self):
        super().__init__("custom_evaluator")
    
    async def evaluate(self, task, history, expected_result=None):
        # Your custom evaluation logic
        score = 0.85  # Calculate based on your criteria
        
        result = EvaluationResult(
            evaluator_name=self.name,
            score=score,
            passed=score >= 0.7,
            metadata={"custom_info": "value"},
        )
        
        self._record_evaluation(result)
        return result
```

## Best Practices

### 1. Session Management
- Always start and complete sessions for proper metrics
- Use unique session IDs (UUID recommended)
- Complete sessions even on errors

### 2. Prompt Versioning
- Use semantic versioning for prompts (major.minor.patch)
- Document changes in metadata
- Test new versions before activating

### 3. Evaluation
- Run evaluations on representative test cases
- Set appropriate thresholds for your use case
- Combine multiple evaluators for comprehensive assessment

### 4. Performance
- Monitor trace overhead in production
- Use sampling for high-volume scenarios
- Archive old metrics regularly

## Example: Complete Workflow

```python
import asyncio
import uuid
from langchain_openai import ChatOpenAI
from browser_ai import Agent
from browser_ai.observability import (
    metrics_collector,
    ComprehensiveEvaluator,
    PromptManager,
)

async def main():
    # Setup
    session_id = str(uuid.uuid4())
    task = "Find the top 3 Python frameworks for web development"
    
    # Initialize prompt manager
    pm = PromptManager()
    
    # Create agent
    llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
    agent = Agent(task=task, llm=llm)
    
    # Start metrics
    metrics_collector.start_session(task=task, session_id=session_id)
    
    try:
        # Run agent (automatically traced)
        history = await agent.run(max_steps=50)
        
        # Complete metrics
        final_metrics = metrics_collector.complete_session(
            session_id=session_id,
            successful=history.is_done(),
        )
        
        # Run evaluation
        evaluator = ComprehensiveEvaluator()
        eval_results = await evaluator.evaluate_all(
            task=task,
            history=history,
        )
        
        # Get summary
        summary = evaluator.get_summary(eval_results)
        
        # Report
        print(f"✅ Task: {task}")
        print(f"📊 Steps: {final_metrics.total_steps}")
        print(f"⚡ Duration: {final_metrics.total_duration_seconds:.2f}s")
        print(f"🎯 Overall Score: {summary['overall_score']:.2f}")
        print(f"✓ All Passed: {summary['all_passed']}")
        
        # Export for analysis
        metrics_collector.export_metrics(f"metrics_{session_id}.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        metrics_collector.complete_session(session_id, successful=False)

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### Traces Not Appearing

1. Verify API key is set:
   ```python
   import os
   print(os.getenv("LMNR_PROJECT_API_KEY"))
   ```

2. Check Laminar initialization:
   ```python
   from lmnr import Laminar
   # Should not raise errors
   ```

3. Ensure network connectivity to Laminar

### High Latency

- Traces are sent asynchronously by default
- Use sampling in high-volume scenarios
- Consider batching for large-scale deployments

### Missing Metrics

- Ensure `metrics_collector.start_session()` is called
- Complete sessions with `complete_session()`
- Check for exceptions in metric recording

## Architecture

```
browser_ai/
├── agent/
│   └── service.py          # @observe on step(), run(), get_next_action()
├── controller/
│   └── service.py          # Span tracking for actions
├── browser/
│   ├── browser.py          # Browser init tracing
│   └── context.py          # State capture tracing
└── observability/          # NEW
    ├── __init__.py
    ├── prompt_manager.py   # Prompt versioning & management
    ├── evaluators.py       # Evaluation framework
    └── metrics.py          # Metrics collection
```

## Resources

- [Laminar Documentation](https://docs.lmnr.ai/)
- [Laminar Python SDK](https://github.com/lmnr-ai/lmnr-python)
- [Browser.AI Documentation](../README.md)

## Support

For issues related to:
- **Laminar**: https://github.com/lmnr-ai/lmnr-python/issues
- **Browser.AI**: https://github.com/browser-ai/browser-ai/issues
