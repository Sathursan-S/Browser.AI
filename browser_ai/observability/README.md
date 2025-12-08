# Observability Module

Comprehensive observability framework for Browser.AI using Laminar.

## Features

- 🔍 **Distributed Tracing**: Track agent execution end-to-end
- 📝 **Prompt Management**: Version control and A/B testing for prompts  
- 📊 **Evaluation Framework**: Measure agent performance and accuracy
- 📈 **Metrics Collection**: Real-time monitoring and aggregated statistics

## Quick Start

### 1. Set up Laminar API Key

```bash
export LMNR_PROJECT_API_KEY="your-api-key"
```

### 2. Run Example

```bash
python examples/observability_example.py
```

### 3. View Traces

Navigate to https://www.lmnr.ai/ to view your traces, metrics, and evaluations.

## Module Structure

```
browser_ai/observability/
├── __init__.py           # Main exports
├── config.py             # Laminar configuration
├── prompt_manager.py     # Prompt versioning system
├── evaluators.py         # Evaluation framework
└── metrics.py            # Metrics collection
```

## Components

### Prompt Manager

Centralized prompt registry with versioning:

```python
from browser_ai.observability import PromptManager, PromptType

pm = PromptManager()

# Register new prompt version
pm.register_prompt(
    prompt_id="my_prompt",
    version="1.0.0",
    prompt_type=PromptType.SYSTEM,
    template="Task: {task}",
    variables=["task"],
)

# Render prompt
text = pm.render_prompt(prompt_id="my_prompt", task="Search Google")
```

### Evaluators

Measure agent performance:

```python
from browser_ai.observability import ComprehensiveEvaluator

evaluator = ComprehensiveEvaluator()
results = await evaluator.evaluate_all(
    task="Search for AI news",
    history=agent.history,
)

print(f"Overall Score: {evaluator.get_summary(results)['overall_score']}")
```

### Metrics Collector

Track execution metrics:

```python
from browser_ai.observability import metrics_collector

# Start tracking
metrics_collector.start_session(task="My task", session_id="123")

# Complete tracking
final_metrics = metrics_collector.complete_session(
    session_id="123",
    successful=True,
)

# Get statistics
stats = metrics_collector.get_aggregated_stats()
```

## Configuration

Set environment variables:

```bash
# Required
LMNR_PROJECT_API_KEY=your-api-key

# Optional
LMNR_ENABLED=true                  # Enable/disable tracing
LMNR_TRACE_SAMPLE_RATE=1.0         # Sampling rate (0.0-1.0)
LMNR_LOG_LEVEL=INFO                # Logging level
```

## Documentation

See [LAMINAR_GUIDE.md](../../docs/observability/LAMINAR_GUIDE.md) for complete documentation.

## Example Output

```
Execution Summary:
  ✓ Success: True
  ✓ Total Steps: 12
  ✓ Total Actions: 28
  ✓ Duration: 45.23 seconds
  ✓ Avg Step Duration: 3.77 seconds

Evaluation Results:
  ✅ Task Success: 0.95
  ✅ Action Accuracy: 0.87
  ✅ Latency: 0.92
  
  Overall Score: 0.91
  All Tests Passed: True
```

## License

Same as Browser.AI project license.
