# Laminar Observability - Quick Reference

## Setup (30 seconds)

```bash
# 1. Get API key from https://www.lmnr.ai/
export LMNR_PROJECT_API_KEY="lm_xxx"

# 2. Run example
python examples/observability_example.py
```

## Import Everything

```python
from browser_ai.observability import (
    # Prompt Management
    PromptManager,
    PromptType,
    PromptVersion,
    
    # Evaluation
    AgentEvaluator,
    TaskSuccessEvaluator,
    ActionAccuracyEvaluator,
    LatencyEvaluator,
    ComprehensiveEvaluator,
    
    # Metrics
    MetricsCollector,
    AgentMetrics,
    metrics_collector,  # Global instance
)
```

## Common Patterns

### Basic Agent with Tracing

```python
from browser_ai import Agent
from langchain_openai import ChatOpenAI

# Tracing is automatic!
agent = Agent(task="Search Google", llm=ChatOpenAI(model='gpt-4o'))
history = await agent.run()
```

### With Metrics

```python
from browser_ai.observability import metrics_collector

session_id = "unique-id"
metrics_collector.start_session(task="My task", session_id=session_id)

# Run agent...

final = metrics_collector.complete_session(session_id, successful=True)
print(f"Steps: {final.total_steps}, Duration: {final.total_duration_seconds}s")
```

### With Evaluation

```python
from browser_ai.observability import ComprehensiveEvaluator

evaluator = ComprehensiveEvaluator()
results = await evaluator.evaluate_all(task="...", history=agent.history)

summary = evaluator.get_summary(results)
print(f"Score: {summary['overall_score']:.2f}, Passed: {summary['all_passed']}")
```

### Prompt Management

```python
from browser_ai.observability import PromptManager, PromptType

pm = PromptManager()

# Register
pm.register_prompt(
    prompt_id="my_prompt",
    version="1.0.0",
    prompt_type=PromptType.SYSTEM,
    template="Task: {task}\nContext: {context}",
    variables=["task", "context"],
)

# Use
text = pm.render_prompt(prompt_id="my_prompt", task="...", context="...")
```

## Environment Variables

```bash
LMNR_PROJECT_API_KEY=lm_xxx        # Required
LMNR_ENABLED=true                  # Optional (default: true)
LMNR_TRACE_SAMPLE_RATE=1.0         # Optional (default: 1.0)
LMNR_LOG_LEVEL=INFO                # Optional (default: INFO)
```

## View Traces

Navigate to: https://www.lmnr.ai/

**Tabs**:
- **Traces**: Full execution flows
- **Spans**: Individual operations  
- **Metrics**: Custom events
- **Prompts**: Prompt usage

## Trace Hierarchy

```
agent.task_execution
├── agent.step.1
│   ├── agent.get_state
│   ├── agent.llm_call
│   └── controller.multi_act
│       └── [actions]
├── agent.step.2
...
```

## Key Spans

| Span | Type | Description |
|------|------|-------------|
| `agent.task_execution` | WORKFLOW | Full task |
| `agent.step.{N}` | DEFAULT | Single step |
| `agent.llm_call` | LLM | Model invocation |
| `controller.multi_act` | TOOL | Action batch |
| `browser.get_state` | DEFAULT | State capture |

## Evaluation Thresholds

| Evaluator | Pass Threshold | Description |
|-----------|----------------|-------------|
| TaskSuccess | 0.7 (70%) | Task completed correctly |
| ActionAccuracy | 0.6 (60%) | Efficient actions |
| Latency | 0.7 (70%) | Performance target |

## Metrics Structure

```python
AgentMetrics(
    task: str,
    session_id: str,
    total_steps: int,
    successful: bool,
    total_actions: int,
    action_breakdown: Dict[str, int],
    total_duration_seconds: float,
    llm_calls: int,
    pages_visited: int,
    unique_domains: List[str],
)
```

## Export Functions

```python
# Metrics
metrics_collector.export_metrics("metrics.json")

# Prompts
pm.export_prompts("prompts.json")
pm.import_prompts("prompts.json")
```

## Custom Tracing

```python
from lmnr import Laminar, observe

@observe(name="my_function")
async def custom_operation():
    with Laminar.start_as_current_span(
        name="detailed_step",
        input={"key": "value"},
        span_type="DEFAULT",
    ):
        result = await do_work()
        Laminar.set_span_output({"result": result})
        return result
```

## Custom Events

```python
from lmnr import Laminar

Laminar.event(
    name="custom_metric",
    value={"metric": "value", "count": 42},
)
```

## Aggregated Stats

```python
stats = metrics_collector.get_aggregated_stats()

# Returns:
{
    "total_sessions": int,
    "successful_sessions": int,
    "success_rate": float,
    "avg_duration_seconds": float,
    "avg_steps_per_session": float,
    "avg_actions_per_session": float,
    "most_used_actions": List[Tuple[str, int]],
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No traces | Check `LMNR_PROJECT_API_KEY` set |
| Import error | Install: `pip install lmnr` |
| Missing data | Complete session lifecycle |
| Slow | Reduce `LMNR_TRACE_SAMPLE_RATE` |

## Files

| Path | Purpose |
|------|---------|
| `browser_ai/observability/` | Core module |
| `docs/observability/LAMINAR_GUIDE.md` | Full guide |
| `examples/observability_example.py` | Working example |

## Next Steps

1. ✅ Set API key
2. ✅ Run example
3. ✅ View in dashboard
4. ✅ Integrate into your code
5. ✅ Customize evaluators

---

**Full Documentation**: `docs/observability/LAMINAR_GUIDE.md`

**Example**: `examples/observability_example.py`

**Dashboard**: https://www.lmnr.ai/
