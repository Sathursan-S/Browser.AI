# Quick Start: Intelligent Website Selection

## What Changed?

Browser.AI now intelligently selects websites instead of always using the same ones (like Daraz or Ikman). The agent can:
- Research the best website for any task
- Try multiple websites if the first one doesn't work
- Handle shopping, downloads, and more across any website

## Quick Examples

### 1. Smart Shopping (Auto-selects best site)
```python
from langchain_openai import ChatOpenAI
from browser_ai.agent.service import Agent

task = "Find and buy wireless earbuds under $50"
llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
agent = Agent(task=task, llm=llm)
result = await agent.run()
```

**What happens**: Agent researches best sites → tries top site → if not found, tries next site → continues until success

### 2. Download Files (Finds safest sources)
```python
task = "Download a Python tutorial PDF for beginners"
agent = Agent(task=task, llm=llm)
result = await agent.run()
```

**What happens**: Agent finds reputable tutorial sites → navigates to best option → downloads PDF

### 3. Multi-Site Search (Automatic fallback)
```python
task = """
Find a vintage record player under $200. 
If not on the first site, try others until you find it.
"""
agent = Agent(task=task, llm=llm)
result = await agent.run()
```

**What happens**: Researches marketplaces → tries eBay → if not found, tries Etsy → continues through 2-3 sites

## New Actions Available

### `find_best_website`
Researches the best website for a specific purpose.

**Use when**: Starting a shopping/download/service task
**Parameters**:
- `purpose`: What you want to do (e.g., "buy gaming laptop")
- `category`: Type of task ("shopping", "download", "service", "other")

### `search_ecommerce` (Enhanced)
Now supports ANY e-commerce site, not just Daraz/Ikman.

**Supported sites**:
- International: Amazon, eBay, AliExpress, Alibaba
- Sri Lankan: Daraz, Ikman, Glomark
- Any custom site: Just specify the domain

**Parameters**:
- `query`: What to search for
- `site`: (Optional) Specific site like "amazon.com" or "ebay.com"

## Task Phrasing Tips

✅ **Better**: "Find the best place to buy a laptop and get me options under $1000"
- Lets agent research and choose

❌ **Old way**: "Go to Daraz and search for laptops"
- Limits to one site

✅ **Better**: "Download a Python tutorial. If the first site doesn't have good ones, try another."
- Enables multi-site strategy

❌ **Old way**: "Download from specific-website.com"
- No fallback

## How to Test

Run the test script:
```bash
python test_intelligent_website_selection.py
```

Or try the examples:
```bash
python examples/intelligent_shopping.py
```

## Benefits

1. **More successful**: Tries multiple sites if first one fails
2. **More flexible**: Works with any website, not just predefined ones
3. **Smarter**: Researches best option for each specific task
4. **Better results**: Finds better deals and more options

## Migration from Old Code

**Before**:
```python
# Always used Daraz
task = "Search for laptops on Daraz"
```

**After**:
```python
# Agent chooses best site
task = "Find the best site to buy laptops in Sri Lanka and search for gaming laptops"
```

The old way still works, but the new way is more powerful!

## Need Help?

- See `INTELLIGENT_WEBSITE_SELECTION.md` for detailed documentation
- Check `examples/intelligent_shopping.py` for more examples
- Review agent logs to see decision-making process

## That's It!

Your agent is now much smarter about finding the right websites. Just ask it to find/buy/download something, and it will figure out the best place to do it! 🚀
