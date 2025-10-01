# Browser.AI LLMOps with Opik Integration

This guide explains how to use the new LLMOps capabilities in Browser.AI with Opik integration for evaluating, testing, and monitoring your browser automation workflows.

## Overview

The Browser.AI Opik integration provides three main LLMOps capabilities:

1. **Evaluation** - Assess LLM performance and task completion quality
2. **Testing** - Run comprehensive test suites with automated scoring
3. **Monitoring** - Track real-time metrics and performance data

## Quick Start

### Basic Setup

```python
from browser_ai.agent.service import Agent
from browser_ai.llmops import OpikConfig, OpikLLMOps
from langchain_openai import ChatOpenAI

# Configure Opik
opik_config = OpikConfig(
    project_name="my-browser-ai-project",
    enabled=True,
    tags=["automation", "testing"]
)

# Create agent with Opik integration
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = Agent(
    task="Go to Google and search for 'OpenAI'",
    llm=llm,
    opik_config=opik_config,
    enable_opik_llmops=True
)

# Run task with automatic monitoring
result = await agent.run(max_steps=10)

# Export monitoring data
opik_data = agent.opik_llmops.export_data()
print(f"Collected {len(opik_data['traces'])} traces")
```

## Features

### 1. Automatic Tracing

Every agent execution is automatically traced with:
- Task input and output
- Step-by-step execution details
- Performance metrics
- Error tracking

```python
# Tracing is automatic when Opik is enabled
agent = Agent(
    task="Navigate to Wikipedia and search for 'Machine Learning'",
    llm=llm,
    enable_opik_llmops=True  # Enables automatic tracing
)
```

### 2. Task Evaluation

Automatically evaluate task completion quality:

```python
from browser_ai.llmops import OpikEvaluator

evaluator = OpikEvaluator(opik_config)

# Evaluate task completion
scores = evaluator.evaluate_task_completion(
    task_description="Search for OpenAI on Google",
    agent_output=result,
    success_criteria=["openai", "search results", "relevant"]
)

print(f"Task completion score: {scores['task_completed']}")
print(f"Criteria fulfillment: {scores['criteria_fulfillment']}")
```

### 3. Performance Monitoring

Track detailed performance metrics:

```python
from browser_ai.llmops import OpikMonitor

monitor = OpikMonitor(opik_config)

# Metrics are automatically collected during execution
# Get summary after task completion
metrics = monitor.get_summary_metrics()

print(f"Total actions: {metrics['total_actions']}")
print(f"Success rate: {1 - metrics['error_rate']:.2%}")
print(f"Average duration: {metrics['average_action_duration']:.2f}ms")
```

### 4. Test Suite Framework

Run comprehensive test suites with multiple scenarios:

```python
from browser_ai.llmops import BrowserAITestSuite, TestScenario

# Create test suite
test_suite = BrowserAITestSuite(
    opik_config=opik_config,
    results_dir="./test_results"
)

# Add test scenarios
scenarios = [
    TestScenario(
        name="google_search",
        task_description="Go to Google and search for 'Browser.AI'",
        success_criteria=["browser", "ai", "search"],
        max_steps=10
    ),
    TestScenario(
        name="wikipedia_navigation", 
        task_description="Navigate to Wikipedia and find the Python page",
        success_criteria=["python", "programming", "wikipedia"],
        max_steps=15
    )
]

for scenario in scenarios:
    test_suite.add_scenario(scenario)

# Run all tests
async def create_agent(task, **kwargs):
    return Agent(
        task=task,
        llm=ChatOpenAI(model="gpt-4o-mini"),
        enable_opik_llmops=True,
        **kwargs
    )

results = await test_suite.run_all_scenarios(create_agent)

# Generate report
test_suite.print_report(results)
```

## Configuration Options

### OpikConfig Parameters

```python
opik_config = OpikConfig(
    project_name="my-project",      # Project name in Opik
    api_key="your-api-key",         # Optional: Opik API key
    workspace="my-workspace",       # Optional: Opik workspace
    enabled=True,                   # Enable/disable Opik integration
    tags=["automation", "testing"]  # Tags for categorization
)
```

### Agent Configuration

```python
agent = Agent(
    task="Your automation task",
    llm=your_llm,
    
    # Opik LLMOps settings
    opik_config=opik_config,        # Opik configuration
    enable_opik_llmops=True,        # Enable Opik integration
    
    # Other agent settings...
    use_vision=True,
    max_actions_per_step=3
)
```

## Test Scenarios

### Creating Test Scenarios

```python
from browser_ai.llmops import TestScenario

scenario = TestScenario(
    name="ecommerce_search",
    task_description="Search for 'laptop' on an e-commerce site and extract top 3 results",
    expected_outcome="List of laptop products with prices",
    success_criteria=["laptop", "price", "$"],
    max_steps=20,
    timeout_seconds=120,
    metadata={"category": "ecommerce", "difficulty": "medium"}
)
```

### Loading Scenarios from File

```json
// test_scenarios.json
[
  {
    "name": "google_search",
    "task_description": "Go to Google and search for 'OpenAI'",
    "success_criteria": ["openai", "results"],
    "max_steps": 10,
    "timeout_seconds": 60
  }
]
```

```python
# Load scenarios from file
test_suite.add_scenarios_from_file("test_scenarios.json")
```

## Evaluation Metrics

The Opik integration automatically tracks various metrics:

### Task-Level Metrics
- **Task Completion Rate**: Percentage of successfully completed tasks
- **Criteria Fulfillment**: How well tasks meet success criteria
- **Error Rate**: Percentage of tasks that encountered errors
- **Duration**: Time taken to complete tasks

### Step-Level Metrics
- **Action Success Rate**: Percentage of successful actions
- **Efficiency Score**: Performance relative to execution time
- **Error Types**: Categorization of different error types

### LLM Metrics
- **Token Usage**: Prompt and completion tokens consumed
- **API Calls**: Number of LLM API calls made
- **Latency**: Response time for LLM calls
- **Cost**: Estimated cost of LLM usage (if available)

## Advanced Usage

### Custom Evaluation Functions

```python
def custom_evaluator(task_description, agent_output, **kwargs):
    """Custom evaluation function"""
    score = 0.0
    
    # Your custom evaluation logic
    if "success" in str(agent_output.extracted_content).lower():
        score += 0.5
    if len(agent_output.extracted_content) > 100:
        score += 0.3
    if not agent_output.error:
        score += 0.2
    
    return {"custom_score": score}

# Use custom evaluator
evaluator = OpikEvaluator(opik_config)
scores = custom_evaluator(task, result)
```

### Batch Testing

```python
# Run multiple test batches
test_batches = [
    {"name": "search_tests", "scenarios": search_scenarios},
    {"name": "form_tests", "scenarios": form_scenarios},
    {"name": "navigation_tests", "scenarios": nav_scenarios}
]

all_results = []
for batch in test_batches:
    print(f"Running {batch['name']}...")
    
    batch_suite = BrowserAITestSuite(opik_config)
    for scenario in batch['scenarios']:
        batch_suite.add_scenario(scenario)
    
    batch_results = await batch_suite.run_all_scenarios(create_agent)
    all_results.extend(batch_results)

# Combined analysis
combined_suite = BrowserAITestSuite(opik_config)
combined_suite.print_report(all_results)
```

### Performance Optimization

```python
# Monitor performance across different configurations
configs = [
    {"model": "gpt-4o-mini", "max_actions": 1},
    {"model": "gpt-4o-mini", "max_actions": 3},
    {"model": "gpt-4o", "max_actions": 1},
]

performance_results = []

for config in configs:
    agent = Agent(
        task="Performance test task",
        llm=ChatOpenAI(model=config["model"]),
        max_actions_per_step=config["max_actions"],
        enable_opik_llmops=True
    )
    
    result = await agent.run(max_steps=10)
    metrics = agent.opik_llmops.monitor.get_summary_metrics()
    
    performance_results.append({
        "config": config,
        "metrics": metrics,
        "success": result.history[-1].result.is_done if result.history else False
    })

# Analyze best configuration
best_config = max(performance_results, 
                 key=lambda x: x['success'] and (1 - x['metrics']['error_rate']))
print(f"Best configuration: {best_config['config']}")
```

## Integration with Existing LMNR

The Opik integration works alongside the existing LMNR observability:

```python
# Both LMNR and Opik will collect data
from lmnr import observe

agent = Agent(
    task="Your task",
    llm=llm,
    enable_opik_llmops=True  # Opik enabled
    # LMNR @observe decorators still work automatically
)

# This gives you dual observability coverage
```

## Data Export and Analysis

### Export Raw Data

```python
# Export all collected data
opik_data = agent.opik_llmops.export_data()

# Save to file for analysis
import json
with open("opik_data.json", "w") as f:
    json.dump(opik_data, f, indent=2)
```

### Generate Reports

```python
# Generate comprehensive test report
test_suite = BrowserAITestSuite(opik_config)
# ... run tests ...
results = await test_suite.run_all_scenarios(create_agent)

# Print formatted report
test_suite.print_report(results)

# Get raw report data
report_data = test_suite.generate_report(results)
print(f"Success rate: {report_data['summary']['success_rate']:.1%}")
```

## Examples

See the `/examples` directory for complete working examples:

- `llmops_demo.py` - Comprehensive demo of all features
- `test_scenarios.json` - Sample test scenarios file

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you have installed Browser.AI with the latest changes
2. **Missing Dependencies**: The integration uses only standard library dependencies
3. **Performance**: For large test suites, consider running tests in smaller batches

### Debug Mode

Enable debug logging to see detailed Opik operations:

```python
import logging
logging.getLogger('browser_ai.llmops').setLevel(logging.DEBUG)

# Now you'll see detailed Opik trace information
```

## Best Practices

1. **Use Descriptive Project Names**: Include version/environment info
2. **Tag Appropriately**: Use tags to categorize different test types
3. **Set Realistic Timeouts**: Allow enough time for complex workflows
4. **Monitor Resource Usage**: Track token consumption and costs
5. **Regular Testing**: Set up automated testing pipelines
6. **Data Retention**: Export and archive important test results

## Future Enhancements

The Opik integration is designed to be extensible. Future enhancements may include:

- Real-time dashboard integration
- A/B testing frameworks
- Advanced anomaly detection
- Integration with CI/CD pipelines
- Custom metric definitions