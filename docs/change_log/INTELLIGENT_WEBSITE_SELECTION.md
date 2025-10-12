# Intelligent Website Selection Feature

## Overview

Browser.AI now includes intelligent website selection capabilities that allow the agent to research and choose the most appropriate websites for shopping, downloading, and other tasks instead of defaulting to pre-configured sites. The agent can also automatically try alternative websites if content is not found on the first site.

## Key Features

### 1. **Dynamic Website Research** (`find_best_website` action)
The agent can research the best websites for any purpose before navigating to them:
- **Shopping**: Finds the best e-commerce sites for specific products
- **Downloads**: Identifies reputable sources for files, documents, software
- **Services**: Discovers appropriate platforms for specific services
- **General Content**: Locates the most relevant websites for any task

### 2. **Flexible E-commerce Support** (Enhanced `search_ecommerce` action)
Supports a wide range of e-commerce platforms:
- **International**: Amazon, eBay, AliExpress, Alibaba
- **Regional**: Daraz (Sri Lanka), Ikman, Glomark
- **Custom Sites**: Can work with any e-commerce site by specifying the domain

### 3. **Multi-Site Fallback Strategy**
The agent automatically:
- Tries multiple websites if content is not found on the first site
- Tracks which sites have been checked in its memory
- Documents why each site failed (no results, out of stock, etc.)
- Continues searching until finding the item or exhausting reasonable alternatives

### 4. **Intelligent Site Selection**
Based on the task context, the agent:
- Researches which websites are most appropriate for the specific product/service
- Considers factors like product category, region, and reputation
- Prioritizes sites based on relevance rather than hardcoded preferences

## Usage Examples

### Example 1: Shopping with Automatic Site Selection

```python
from langchain_openai import ChatOpenAI
from browser_ai.agent.service import Agent

task = """
I want to buy a gaming laptop. Find the best website to purchase it from,
search for gaming laptops on that site, and show me the top 3 options with prices.
If the first website doesn't have good options, try another website.
"""

llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
agent = Agent(task=task, llm=llm)
result = await agent.run()
```

**Agent Workflow**:
1. Calls `find_best_website` to research best sites for gaming laptops
2. Reviews search results and identifies top e-commerce platforms
3. Navigates to the most appropriate site
4. Searches for gaming laptops
5. If results are unsatisfactory, tries the next best site
6. Returns top 3 options found

### Example 2: Download with Source Research

```python
task = """
I need to download a comprehensive Python programming tutorial PDF 
for beginners. First research the best websites for downloading 
programming tutorials, then find and download a good Python PDF guide.
"""

agent = Agent(task=task, llm=llm)
result = await agent.run()
```

**Agent Workflow**:
1. Uses `find_best_website` with category="download"
2. Identifies reputable educational resource sites
3. Navigates to the most appropriate platform
4. Searches for Python tutorial PDFs
5. Downloads the best match

### Example 3: Multi-Site Product Search

```python
task = """
Find a vintage vinyl record player from the 1960s with a price under $200. 
If it's not available on the first website, automatically search other 
marketplaces until you find it or try at least 3 different sites.
"""

agent = Agent(task=task, llm=llm)
result = await agent.run()
```

**Agent Workflow**:
1. Researches best sites for vintage electronics
2. Creates list of 3+ potential marketplaces
3. Tries first site (e.g., eBay)
4. If not found: "Memory: eBay - no results. Trying Etsy (2/3)"
5. Searches second site
6. Continues until product is found or alternatives exhausted

## How It Works

### The `find_best_website` Action

**Parameters**:
- `purpose`: What you want to do (e.g., "buy gaming laptop", "download python tutorial")
- `category`: One of: "shopping", "download", "information", "service", "other"

**Behavior**:
- Constructs an intelligent Google search query
- Searches for "best website to [purpose]"
- Returns search results showing top recommended websites
- Agent reviews results and creates a prioritized list

**Example Action**:
```json
{
  "find_best_website": {
    "purpose": "buy wireless earbuds under $50",
    "category": "shopping"
  }
}
```

### The Enhanced `search_ecommerce` Action

**Parameters**:
- `query`: Product search query
- `site`: (Optional) Specific e-commerce site to use

**Supported Sites**:
- `daraz.lk` or `daraz`
- `ikman.lk` or `ikman`
- `glomark.lk` or `glomark`
- `amazon.com` or `amazon`
- `ebay.com` or `ebay`
- `aliexpress.com` or `aliexpress`
- `alibaba.com` or `alibaba`
- Any custom domain (will attempt generic search URL construction)

**Example Actions**:
```json
// Use default site
{"search_ecommerce": {"query": "gaming laptop"}}

// Specify site
{"search_ecommerce": {"query": "wireless mouse", "site": "amazon.com"}}

// Try alternative site
{"search_ecommerce": {"query": "headphones", "site": "ebay.com"}}
```

## Agent Memory Tracking

The agent maintains detailed memory of its multi-site search strategy:

```json
{
  "current_state": {
    "memory": "Researched best sites for gaming laptops: Amazon, Newegg, Best Buy. Tried Amazon - found 15 options but all over budget. Now trying Newegg (site 2/3). Still need to check Best Buy if needed.",
    "next_goal": "Search Newegg for gaming laptops under $1000"
  }
}
```

## Integration with Existing Features

### Automatic Scrolling
If expected elements aren't found (e.g., "Add to Cart" buttons), the agent automatically:
- Scrolls down 2-3 times to look for missing elements
- Tries scrolling up if still not found
- Uses `scroll_to_text` for specific known text

### CAPTCHA Handling
When encountering CAPTCHAs during multi-site searches:
- Agent uses `request_user_help` instead of attempting to solve
- User solves CAPTCHA
- Agent continues with the same site or moves to next alternative

### Error Recovery
If a site fails to load or has technical issues:
- Agent notes the failure in memory
- Automatically tries the next site in the list
- Doesn't count technical failures against the site's viability

## Prompt Guidance

The agent is guided by enhanced prompts that emphasize:

1. **Research First**: Always use `find_best_website` before shopping/downloading
2. **Multi-Site Strategy**: Keep a list of alternatives, try at least 2-3 sites
3. **Memory Tracking**: Document each attempt with site name and outcome
4. **Persistence**: Don't give up after one site - explore alternatives
5. **Flexibility**: Use different search terms on different sites if needed

## Configuration

No additional configuration required! The feature works out of the box with existing Agent setup:

```python
agent = Agent(
    task="Your task here",
    llm=your_llm_model,
    # All existing parameters work as before
)
```

## Best Practices

### For Shopping Tasks
✅ **Good**: "Find and buy the best wireless earbuds under $50"
- Agent researches sites, compares options, tries multiple platforms

❌ **Avoid**: "Go to Amazon and buy earbuds"
- Limits agent to one site, misses potentially better options

### For Download Tasks
✅ **Good**: "Download a beginner Python tutorial PDF"
- Agent finds reputable educational sites

❌ **Avoid**: "Go to random-download-site.com and get Python PDF"
- May miss safer, better quality sources

### For Product Not Found Scenarios
✅ **Good**: "Find a vintage camera. Try multiple sites if needed."
- Agent automatically implements multi-site strategy

❌ **Avoid**: "Search only on eBay for vintage camera"
- No fallback if item not found

## Advanced Use Cases

### Cross-Site Price Comparison
```python
task = """
I want to buy wireless earbuds under $50. Research the best e-commerce 
sites for electronics, then search on the top 3 sites. Compare prices 
and show me the best deal across all sites.
"""
```

### Region-Specific Shopping
```python
task = """
Find the best website to buy electronics in Sri Lanka, then search 
for a smartphone under LKR 50,000. If not available, try international 
sites that ship to Sri Lanka.
"""
```

### Specialized Downloads
```python
task = """
Find the best website to download free, legal stock photos. Then 
download 5 high-quality nature photos.
"""
```

## Troubleshooting

### Issue: Agent Defaults to Specific Site
**Solution**: Make sure task explicitly mentions "find the best website" or "research where to buy"

### Issue: Agent Gives Up Too Quickly
**Solution**: Add "try at least 3 different websites" to your task

### Issue: Agent Chooses Inappropriate Sites
**Solution**: Provide more context in the task about product category, region, or budget

### Issue: Too Many Sites Being Tried
**Solution**: The agent typically tries 2-3 sites by default. Specify a limit: "try up to 2 websites"

## Migration Guide

### Old Approach (Hardcoded Sites)
```python
# Before: Task assumed specific sites
task = "Search for laptops on Daraz"
```

### New Approach (Intelligent Selection)
```python
# After: Agent researches and selects best site
task = "Find the best website to buy laptops in Sri Lanka, then search for gaming laptops"
```

## API Reference

### `FindBestWebsiteAction`
```python
class FindBestWebsiteAction(BaseModel):
    purpose: str  # What you want to do
    category: str  # "shopping", "download", "information", "service", "other"
```

### `SearchEcommerceAction` (Enhanced)
```python
class SearchEcommerceAction(BaseModel):
    query: str  # Product search query
    site: Optional[str] = None  # Any e-commerce domain or None for default
```

## Performance Considerations

- **Initial Research**: `find_best_website` adds 1 additional step (Google search)
- **Multi-Site Attempts**: Each site attempt is a separate navigation
- **Token Usage**: Memory tracking increases context slightly but improves success rate
- **Success Rate**: Significantly higher for finding niche or region-specific items

## Future Enhancements

Potential improvements being considered:
- Caching of best websites for common product categories
- Integration with price comparison APIs
- Automatic detection of better deals across sites
- Learning from past successful site selections
- Regional preference configuration

## Support

For issues or questions about intelligent website selection:
1. Check the `examples/intelligent_shopping.py` file for working examples
2. Review agent logs for decision-making process
3. Verify `find_best_website` is being called before site navigation
4. Ensure task includes clear intent for multi-site search if needed

## Summary

The intelligent website selection feature transforms Browser.AI from a tool that requires explicit site specification to one that can research, select, and try multiple websites automatically. This makes the agent more autonomous, flexible, and successful at finding content across the web.
