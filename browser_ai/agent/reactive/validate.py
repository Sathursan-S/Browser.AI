#!/usr/bin/env python3
"""
Validation script for the reactive agents implementation.

This script validates the structure and basic functionality without requiring
all dependencies to be installed.
"""

import os
import sys
import importlib.util
from pathlib import Path

def validate_file_structure():
    """Validate that all required files are present"""
    
    base_path = Path(__file__).parent
    
    required_files = [
        'base_reactive.py',
        'langgraph_agent.py', 
        'crewai_agent.py',
        '__init__.py',
        'README.md',
        'context7_integration.md',
        'examples/basic_usage.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        file_path = base_path / file
        if not file_path.exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("✅ All required files are present")
        return True


def validate_python_syntax():
    """Validate Python syntax of all Python files"""
    
    base_path = Path(__file__).parent
    
    python_files = [
        'base_reactive.py',
        'langgraph_agent.py',
        'crewai_agent.py',
        '__init__.py',
        'examples/basic_usage.py'
    ]
    
    syntax_errors = []
    
    for file in python_files:
        file_path = base_path / file
        
        if not file_path.exists():
            continue
            
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            
            compile(source, str(file_path), 'exec')
            print(f"✅ {file}: Syntax OK")
            
        except SyntaxError as e:
            syntax_errors.append((file, str(e)))
            print(f"❌ {file}: Syntax Error - {e}")
        except Exception as e:
            syntax_errors.append((file, str(e)))
            print(f"❌ {file}: Error - {e}")
    
    if syntax_errors:
        print(f"\n❌ Found {len(syntax_errors)} syntax errors")
        return False
    else:
        print("\n✅ All Python files have valid syntax")
        return True


def validate_class_structure():
    """Validate that classes are properly defined"""
    
    base_path = Path(__file__).parent
    
    # Check base_reactive.py
    base_reactive_path = base_path / 'base_reactive.py'
    
    try:
        with open(base_reactive_path, 'r') as f:
            content = f.read()
        
        # Check for key classes and methods
        required_elements = [
            'class ReactiveEvent',
            'class ReactiveState', 
            'class BaseReactiveAgent',
            'async def reactive_step',
            'async def get_recovery_action',
            'async def execute_recovery_action',
            'async def emit_event',
            'def subscribe_to_event'
        ]
        
        missing_elements = []
        
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print("❌ Missing elements in base_reactive.py:")
            for element in missing_elements:
                print(f"  - {element}")
            return False
        else:
            print("✅ BaseReactiveAgent has all required methods")
            
    except Exception as e:
        print(f"❌ Error checking base_reactive.py: {e}")
        return False
    
    # Check LangGraph agent
    langgraph_path = base_path / 'langgraph_agent.py'
    
    try:
        with open(langgraph_path, 'r') as f:
            content = f.read()
        
        if 'class LangGraphReactiveAgent' not in content:
            print("❌ LangGraphReactiveAgent class not found")
            return False
        else:
            print("✅ LangGraphReactiveAgent class defined")
            
    except Exception as e:
        print(f"❌ Error checking langgraph_agent.py: {e}")
        return False
    
    # Check CrewAI agent
    crewai_path = base_path / 'crewai_agent.py'
    
    try:
        with open(crewai_path, 'r') as f:
            content = f.read()
        
        if 'class CrewAIReactiveAgent' not in content:
            print("❌ CrewAIReactiveAgent class not found")
            return False
        else:
            print("✅ CrewAIReactiveAgent class defined")
            
    except Exception as e:
        print(f"❌ Error checking crewai_agent.py: {e}")
        return False
    
    return True


def validate_documentation():
    """Validate documentation files"""
    
    base_path = Path(__file__).parent
    
    # Check README.md
    readme_path = base_path / 'README.md'
    
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
        
        required_sections = [
            '# Reactive Agents for Browser.AI',
            '## Overview',
            '## Agent Types', 
            '## Installation',
            '## Quick Start',
            '## Examples'
        ]
        
        missing_sections = []
        
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print("❌ Missing sections in README.md:")
            for section in missing_sections:
                print(f"  - {section}")
            return False
        else:
            print("✅ README.md has all required sections")
            
    except Exception as e:
        print(f"❌ Error checking README.md: {e}")
        return False
    
    # Check Context7 integration doc
    context7_path = base_path / 'context7_integration.md'
    
    try:
        with open(context7_path, 'r') as f:
            content = f.read()
        
        if '# Reactive Agent Integration with Context7' not in content:
            print("❌ Context7 integration document missing title")
            return False
        else:
            print("✅ Context7 integration document properly structured")
            
    except Exception as e:
        print(f"❌ Error checking context7_integration.md: {e}")
        return False
    
    return True


def validate_examples():
    """Validate example files"""
    
    base_path = Path(__file__).parent / 'examples'
    
    if not base_path.exists():
        print("❌ Examples directory not found")
        return False
    
    example_file = base_path / 'basic_usage.py'
    
    try:
        with open(example_file, 'r') as f:
            content = f.read()
        
        required_examples = [
            'async def langraph_web_scraping_example',
            'async def crewai_collaborative_browsing_example',
            'async def event_driven_monitoring_example',
            'async def error_recovery_example'
        ]
        
        missing_examples = []
        
        for example in required_examples:
            if example not in content:
                missing_examples.append(example)
        
        if missing_examples:
            print("❌ Missing examples in basic_usage.py:")
            for example in missing_examples:
                print(f"  - {example}")
            return False
        else:
            print("✅ All required examples are present")
            
    except Exception as e:
        print(f"❌ Error checking examples: {e}")
        return False
    
    return True


def main():
    """Run all validation checks"""
    
    print("🔍 Validating Reactive Agents Implementation")
    print("=" * 50)
    
    checks = [
        ("File Structure", validate_file_structure),
        ("Python Syntax", validate_python_syntax), 
        ("Class Structure", validate_class_structure),
        ("Documentation", validate_documentation),
        ("Examples", validate_examples)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        print("-" * 20)
        
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error during {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:20} {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All validations passed! The reactive agents implementation is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)