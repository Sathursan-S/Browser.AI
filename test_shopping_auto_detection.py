"""
Test Shopping Task Auto-Detection
Verifies that shopping tasks automatically inject location detection actions.
"""

import asyncio
from browser_ai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()


async def test_shopping_detection():
    """Test that shopping keywords trigger auto-injection"""
    print("\n" + "="*60)
    print("TEST: Shopping Task Auto-Detection")
    print("="*60 + "\n")
    
    # Test Case 1: Shopping task should inject actions
    print("Test Case 1: Shopping Task Detection")
    print("-" * 60)
    
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', temperature=0.0)
    agent = Agent(
        task="buy wireless headphones under $100",
        llm=llm
    )
    
    print(f"Task: {agent.task}")
    print(f"Initial Actions Injected: {agent.initial_actions is not None}")
    
    if agent.initial_actions:
        print(f"Number of Initial Actions: {len(agent.initial_actions)}")
        print("\nInitial Actions:")
        for i, action in enumerate(agent.initial_actions, 1):
            # Get action name and params
            action_dict = action.model_dump(exclude_unset=True)
            action_name = list(action_dict.keys())[0]
            action_params = action_dict[action_name]
            print(f"  {i}. {action_name}: {action_params}")
    else:
        print("❌ FAILED: No initial actions injected!")
        return False
    
    # Verify correct actions were injected
    action_names = [list(a.model_dump(exclude_unset=True).keys())[0] for a in agent.initial_actions]
    
    expected_actions = ['detect_location', 'find_best_website']
    if action_names == expected_actions:
        print("\n✅ PASSED: Correct actions injected in correct order")
    else:
        print(f"\n❌ FAILED: Expected {expected_actions}, got {action_names}")
        return False
    
    # Test Case 2: Non-shopping task should NOT inject actions
    print("\n\nTest Case 2: Non-Shopping Task (No Injection)")
    print("-" * 60)
    
    agent2 = Agent(
        task="check the weather in Tokyo",
        llm=llm
    )
    
    print(f"Task: {agent2.task}")
    print(f"Initial Actions Injected: {agent2.initial_actions is not None}")
    
    if agent2.initial_actions is None:
        print("✅ PASSED: No actions injected for non-shopping task")
    else:
        print("❌ FAILED: Actions were injected for non-shopping task!")
        return False
    
    # Test Case 3: Various shopping keywords
    print("\n\nTest Case 3: Different Shopping Keywords")
    print("-" * 60)
    
    shopping_tasks = [
        "purchase a laptop",
        "find me the best phone",
        "order pizza online",
        "get me a camera under $500",
        "shop for running shoes",
        "what's the price of iPhone 15",
    ]
    
    all_detected = True
    for task in shopping_tasks:
        agent_test = Agent(task=task, llm=llm)
        detected = agent_test.initial_actions is not None
        status = "✅" if detected else "❌"
        print(f"{status} '{task}' → Detected: {detected}")
        if not detected:
            all_detected = False
    
    if all_detected:
        print("\n✅ PASSED: All shopping keywords detected correctly")
    else:
        print("\n❌ FAILED: Some shopping keywords not detected")
        return False
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED ✅")
    print("="*60 + "\n")
    return True


async def test_manual_override():
    """Test that manual initial_actions override auto-detection"""
    print("\n" + "="*60)
    print("TEST: Manual Override of Auto-Detection")
    print("="*60 + "\n")
    
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', temperature=0.0)
    
    # Provide custom initial actions - should override auto-detection
    custom_actions = [
        {"go_to_url": {"url": "https://amazon.com"}}
    ]
    
    agent = Agent(
        task="buy headphones",  # This would normally trigger auto-detection
        llm=llm,
        initial_actions=custom_actions
    )
    
    print(f"Task: {agent.task}")
    print(f"Custom Actions Provided: {custom_actions}")
    print(f"Number of Initial Actions: {len(agent.initial_actions) if agent.initial_actions else 0}")
    
    if agent.initial_actions:
        action_dict = agent.initial_actions[0].model_dump(exclude_unset=True)
        action_name = list(action_dict.keys())[0]
        
        if action_name == 'go_to_url':
            print("✅ PASSED: Custom actions override auto-detection")
            return True
        else:
            print(f"❌ FAILED: Expected 'go_to_url', got '{action_name}'")
            return False
    else:
        print("❌ FAILED: No initial actions found")
        return False


if __name__ == "__main__":
    print("\n🧪 Starting Shopping Auto-Detection Tests...\n")
    
    # Run tests
    test1_result = asyncio.run(test_shopping_detection())
    test2_result = asyncio.run(test_manual_override())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Shopping Detection Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Manual Override Test: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print("="*60 + "\n")
    
    if test1_result and test2_result:
        print("🎉 All tests passed! Shopping auto-detection is working correctly.\n")
        exit(0)
    else:
        print("❌ Some tests failed. Please review the output above.\n")
        exit(1)
