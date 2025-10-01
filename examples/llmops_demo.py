#!/usr/bin/env python3
"""
Example script demonstrating Browser.AI with Opik LLMOps integration

This script shows how to:
1. Set up Opik for monitoring Browser.AI agents
2. Run evaluation tests with different scenarios
3. Generate performance reports and metrics
4. Export data for further analysis
"""

import asyncio
import os
import logging
from typing import Any

# Import Browser.AI components
from browser_ai.agent.service import Agent
from browser_ai.browser.browser import Browser
from browser_ai.controller.service import Controller

# Import LLMOps components
from browser_ai.llmops import (
    OpikConfig, 
    OpikLLMOps, 
    BrowserAITestSuite, 
    TestScenario,
    create_sample_scenarios
)

# Import LangChain models (you'll need these installed)
from langchain_openai import ChatOpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_agent_with_opik(task: str, **kwargs) -> Agent:
    """Factory function to create an agent with Opik integration"""
    
    # Configure Opik
    opik_config = OpikConfig(
        project_name="browser-ai-evaluation",
        enabled=True,
        tags=["demo", "evaluation", "browser-ai"]
    )
    
    # Set up LLM (you'll need to set your API key)
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Use a cost-effective model for testing
        temperature=0,
        max_tokens=4000
    )
    
    # Create browser instance
    browser = Browser()
    browser_context = await browser.new_context()
    
    # Create controller with Opik integration
    opik_llmops = OpikLLMOps(opik_config)
    controller = Controller(opik_llmops=opik_llmops)
    
    # Create agent with Opik configuration
    agent = Agent(
        task=task,
        llm=llm,
        browser_context=browser_context,
        controller=controller,
        opik_config=opik_config,
        enable_opik_llmops=True,
        use_vision=True,
        max_actions_per_step=3,
        **kwargs
    )
    
    return agent

async def run_single_task_demo():
    """Demonstrate running a single task with Opik monitoring"""
    logger.info("Running single task demo with Opik monitoring...")
    
    task = "Go to Google and search for 'Browser.AI automation'"
    agent = await create_agent_with_opik(task)
    
    try:
        # Run the task
        result = await agent.run(max_steps=10)
        
        # Export Opik data for analysis
        if agent.opik_llmops:
            opik_data = agent.opik_llmops.export_data()
            logger.info("Opik monitoring data:")
            logger.info(f"Traces collected: {len(opik_data['traces'])}")
            logger.info(f"Evaluations: {len(opik_data['evaluations'])}")
            logger.info(f"Metrics summary: {opik_data['metrics_summary']}")
        
        logger.info(f"Task completed in {len(result.history)} steps")
        return result
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return None
        
    finally:
        # Cleanup
        if hasattr(agent, 'browser_context'):
            await agent.browser_context.close()

async def run_test_suite_demo():
    """Demonstrate running a comprehensive test suite"""
    logger.info("Running test suite demo with Opik evaluation...")
    
    # Configure Opik for testing
    opik_config = OpikConfig(
        project_name="browser-ai-test-suite",
        enabled=True,
        tags=["test-suite", "evaluation", "automation"]
    )
    
    # Create test suite
    test_suite = BrowserAITestSuite(
        opik_config=opik_config,
        results_dir="./test_results"
    )
    
    # Add sample scenarios
    scenarios = create_sample_scenarios()
    for scenario in scenarios:
        test_suite.add_scenario(scenario)
    
    # Add custom scenarios
    custom_scenarios = [
        TestScenario(
            name="github_search",
            task_description="Go to GitHub and search for 'browser automation' repositories",
            success_criteria=["repository", "automation"],
            max_steps=15,
            timeout_seconds=120
        ),
        TestScenario(
            name="news_headline_extraction",
            task_description="Visit a news website and extract the top 3 headlines",
            success_criteria=["headline", "news"],
            max_steps=20,
            timeout_seconds=180
        )
    ]
    
    for scenario in custom_scenarios:
        test_suite.add_scenario(scenario)
    
    try:
        # Run all test scenarios
        results = await test_suite.run_all_scenarios(
            agent_factory=create_agent_with_opik,
            max_actions_per_step=3,
            use_vision=True
        )
        
        # Generate and print report
        test_suite.print_report(results)
        
        # Export detailed data
        for i, result in enumerate(results):
            if result.scenario.name == "github_search":
                logger.info(f"GitHub search result: {result.extracted_content[:200]}...")
                
        return results
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return []

async def run_performance_monitoring_demo():
    """Demonstrate performance monitoring capabilities"""
    logger.info("Running performance monitoring demo...")
    
    # Configure Opik for performance monitoring
    opik_config = OpikConfig(
        project_name="browser-ai-performance",
        enabled=True,
        tags=["performance", "monitoring", "metrics"]
    )
    
    tasks = [
        "Search for 'machine learning' on Google",
        "Navigate to Wikipedia and find the Python programming page",
        "Go to Stack Overflow and search for browser automation questions"
    ]
    
    performance_results = []
    
    for i, task in enumerate(tasks):
        logger.info(f"Running performance test {i+1}/{len(tasks)}: {task}")
        
        agent = await create_agent_with_opik(task)
        
        try:
            result = await agent.run(max_steps=15)
            
            # Collect performance metrics
            if agent.opik_llmops:
                metrics = agent.opik_llmops.monitor.get_summary_metrics()
                performance_results.append({
                    "task": task,
                    "steps": len(result.history),
                    "metrics": metrics
                })
                
            await agent.browser_context.close()
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
    
    # Analyze performance results
    logger.info("\nPerformance Analysis:")
    for result in performance_results:
        logger.info(f"Task: {result['task'][:50]}...")
        logger.info(f"  Steps taken: {result['steps']}")
        logger.info(f"  Total actions: {result['metrics'].get('total_actions', 0)}")
        logger.info(f"  Success rate: {1 - result['metrics'].get('error_rate', 0):.2%}")
        logger.info(f"  Avg action duration: {result['metrics'].get('average_action_duration', 0):.2f}ms")
        logger.info("")
    
    return performance_results

async def main():
    """Main function to run all demos"""
    logger.info("Starting Browser.AI + Opik LLMOps Demo")
    logger.info("="*60)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set. Please set it to run this demo.")
        logger.info("You can set it with: export OPENAI_API_KEY='your-api-key'")
        return
    
    try:
        # Demo 1: Single task with monitoring
        logger.info("\n🚀 Demo 1: Single Task with Opik Monitoring")
        await run_single_task_demo()
        
        # Demo 2: Test suite evaluation
        logger.info("\n🧪 Demo 2: Test Suite Evaluation")
        await run_test_suite_demo()
        
        # Demo 3: Performance monitoring
        logger.info("\n📊 Demo 3: Performance Monitoring")
        await run_performance_monitoring_demo()
        
        logger.info("\n✅ All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        
    logger.info("\n" + "="*60)
    logger.info("Browser.AI + Opik LLMOps Demo Complete")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())