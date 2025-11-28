"""
Test script to verify intelligent website selection features.

This script tests:
1. FindBestWebsiteAction model
2. Enhanced SearchEcommerceAction with multiple sites
3. Multi-site search workflow
"""

import asyncio

from browser_ai.browser.browser import Browser
from browser_ai.browser.context import BrowserContext
from browser_ai.controller.service import Controller
from browser_ai.controller.views import FindBestWebsiteAction, SearchEcommerceAction


async def test_action_models():
    """Test that the new action models are properly defined."""
    print("Testing Action Models...")
    
    # Test FindBestWebsiteAction
    try:
        action1 = FindBestWebsiteAction(
            purpose="buy gaming laptop",
            category="shopping"
        )
        print(f"✓ FindBestWebsiteAction created: {action1}")
    except Exception as e:
        print(f"✗ FindBestWebsiteAction failed: {e}")
        return False
    
    # Test SearchEcommerceAction with various sites
    try:
        action2 = SearchEcommerceAction(query="laptop", site="amazon.com")
        print(f"✓ SearchEcommerceAction (Amazon): {action2}")
        
        action3 = SearchEcommerceAction(query="laptop", site="ebay.com")
        print(f"✓ SearchEcommerceAction (eBay): {action3}")
        
        action4 = SearchEcommerceAction(query="laptop")  # No site specified
        print(f"✓ SearchEcommerceAction (default): {action4}")
    except Exception as e:
        print(f"✗ SearchEcommerceAction failed: {e}")
        return False
    
    print("\n✓ All action models are properly defined!\n")
    return True


async def test_controller_actions():
    """Test that the controller has the new actions registered."""
    print("Testing Controller Actions...")
    
    try:
        controller = Controller()
        actions = controller.registry.registry
        
        # Check for find_best_website
        find_best_website_found = any('find_best_website' in str(action) for action in actions)
        if find_best_website_found:
            print("✓ find_best_website action is registered")
        else:
            print("✗ find_best_website action NOT found")
            return False
        
        # Check for search_ecommerce
        search_ecommerce_found = any('search_ecommerce' in str(action) for action in actions)
        if search_ecommerce_found:
            print("✓ search_ecommerce action is registered")
        else:
            print("✗ search_ecommerce action NOT found")
            return False
        
        print(f"\n✓ Controller has {len(actions)} total actions registered!\n")
        return True
    except Exception as e:
        print(f"✗ Controller test failed: {e}")
        return False


async def test_find_best_website_execution():
    """Test executing find_best_website action."""
    print("Testing find_best_website Execution...")
    
    try:
        browser = Browser()
        await browser.start()
        context = BrowserContext(browser=browser)
        controller = Controller()
        
        # Get the find_best_website action
        actions = controller.registry.registry
        find_best_website_action = None
        for action_name, action_func in actions.items():
            if 'find_best_website' in action_name:
                find_best_website_action = action_func
                break
        
        if not find_best_website_action:
            print("✗ Could not find find_best_website action")
            await browser.close()
            return False
        
        # Execute the action
        params = FindBestWebsiteAction(
            purpose="buy wireless earbuds",
            category="shopping"
        )
        
        result = await find_best_website_action(params, context)
        print("✓ Action executed successfully!")
        print(f"  Result: {result.extracted_content[:100]}...")
        
        await browser.close()
        print("\n✓ find_best_website execution test passed!\n")
        return True
        
    except Exception as e:
        print(f"✗ Execution test failed: {e}")
        try:
            await browser.close()
        except:
            pass
        return False


async def test_search_ecommerce_multiple_sites():
    """Test search_ecommerce with different site parameters."""
    print("Testing search_ecommerce with Multiple Sites...")
    
    test_sites = [
        ("amazon.com", "gaming laptop"),
        ("ebay.com", "vintage camera"),
        ("daraz.lk", "smartphone"),
        (None, "headphones"),  # Test default
    ]
    
    try:
        browser = Browser()
        await browser.start()
        context = BrowserContext(browser=browser)
        controller = Controller()
        
        # Get the search_ecommerce action
        actions = controller.registry.registry
        search_ecommerce_action = None
        for action_name, action_func in actions.items():
            if 'search_ecommerce' in action_name:
                search_ecommerce_action = action_func
                break
        
        if not search_ecommerce_action:
            print("✗ Could not find search_ecommerce action")
            await browser.close()
            return False
        
        for site, query in test_sites:
            params = SearchEcommerceAction(query=query, site=site)
            result = await search_ecommerce_action(params, context)
            site_name = site if site else "default"
            print(f"✓ Tested {site_name}: {result.extracted_content}")
            await asyncio.sleep(1)  # Small delay between requests
        
        await browser.close()
        print("\n✓ Multi-site search_ecommerce test passed!\n")
        return True
        
    except Exception as e:
        print(f"✗ Multi-site test failed: {e}")
        try:
            await browser.close()
        except:
            pass
        return False


async def run_all_tests():
    """Run all test suites."""
    print("=" * 80)
    print("INTELLIGENT WEBSITE SELECTION - TEST SUITE")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Action Models
    results.append(await test_action_models())
    
    # Test 2: Controller Registration
    results.append(await test_controller_actions())
    
    # Test 3: Find Best Website Execution (requires browser)
    print("Note: The following tests will open a browser window.")
    user_input = input("Continue with browser tests? (y/n): ")
    if user_input.lower() == 'y':
        results.append(await test_find_best_website_execution())
        results.append(await test_search_ecommerce_multiple_sites())
    else:
        print("Skipping browser tests.")
    
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED! 🎉")
        print("\nThe intelligent website selection feature is working correctly.")
        print("You can now use find_best_website and enhanced search_ecommerce actions.")
    else:
        print(f"\n✗ Some tests failed ({total - passed} failures)")
        print("Please check the error messages above.")
    
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(run_all_tests())
