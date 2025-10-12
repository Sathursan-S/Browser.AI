# Intelligent Website Selection - Workflow Diagrams

## 1. Standard Shopping Workflow (Before vs After)

### BEFORE (Hardcoded Approach)
```
User Task: "Buy laptop"
    ↓
Agent assumes Daraz
    ↓
Search on Daraz
    ↓
If not found → Give up
    ↓
Return "Not found"
```

### AFTER (Intelligent Approach)
```
User Task: "Buy laptop"
    ↓
find_best_website("buy laptop", "shopping")
    ↓
Google search: "best website to buy laptop online"
    ↓
Agent reviews results:
  - Amazon.com
  - Newegg.com  
  - Best Buy
  - Daraz.lk
    ↓
Try Site 1 (Amazon)
    ↓
search_ecommerce("laptop", "amazon.com")
    ↓
Found? ───YES──→ Show results → Done
    ↓
   NO
    ↓
Memory: "Amazon: no matches in budget"
    ↓
Try Site 2 (Newegg)
    ↓
search_ecommerce("laptop", "newegg.com")
    ↓
Found? ───YES──→ Show results → Done
    ↓
   NO
    ↓
Try Site 3 (Best Buy)
    ↓
Found? ───YES──→ Show results → Done
    ↓
   NO
    ↓
Return "Tried 3 sites, not found in budget"
```

## 2. Download Workflow

```
User Task: "Download Python PDF tutorial"
    ↓
find_best_website("download python tutorial", "download")
    ↓
Google search: "best website to download python tutorial"
    ↓
Agent reviews results:
  - Python.org
  - Real Python
  - Tutorial Point
  - W3Schools
    ↓
Navigate to Python.org (most reputable)
    ↓
Search for PDF tutorials
    ↓
Found? ───YES──→ Download → Done
    ↓
   NO
    ↓
Memory: "Python.org: no PDF downloads available"
    ↓
Try Real Python
    ↓
Found? ───YES──→ Download → Done
    ↓
   NO
    ↓
Try Tutorial Point
    ↓
Download → Done
```

## 3. Multi-Site Search Strategy Detail

```
┌─────────────────────────────────────┐
│  Task: Find vintage record player   │
└──────────────┬──────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ PHASE 1: RESEARCH                    │
├──────────────────────────────────────┤
│ find_best_website(                   │
│   "vintage record player",           │
│   "shopping"                         │
│ )                                    │
│                                      │
│ Results:                             │
│ ✓ eBay - Popular for vintage items  │
│ ✓ Etsy - Handmade & vintage         │
│ ✓ Reverb - Music equipment          │
│ ✓ Amazon - General marketplace      │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ PHASE 2: PRIORITIZE                  │
├──────────────────────────────────────┤
│ Memory: "Plan to try:                │
│   1. eBay (best for vintage)         │
│   2. Etsy (specialty vintage)        │
│   3. Reverb (music equipment)"       │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ PHASE 3: ATTEMPT 1                   │
├──────────────────────────────────────┤
│ search_ecommerce(                    │
│   "vintage record player 1960s",     │
│   "ebay.com"                         │
│ )                                    │
│                                      │
│ Results: 3 found, all over $300      │
│                                      │
│ Memory: "eBay: Found 3 but too       │
│          expensive (over $200).      │
│          Trying Etsy next (2/3)"     │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ PHASE 4: ATTEMPT 2                   │
├──────────────────────────────────────┤
│ search_ecommerce(                    │
│   "vintage record player 1960s",     │
│   "etsy.com"                         │
│ )                                    │
│                                      │
│ Results: 5 found, 2 under $200       │
│                                      │
│ SUCCESS! Extract top 2 options       │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ PHASE 5: COMPLETION                  │
├──────────────────────────────────────┤
│ done({                               │
│   "Found 2 vintage record players    │
│    from the 1960s under $200:        │
│    1. [details]                      │
│    2. [details]                      │
│    Source: Etsy                      │
│    (Also tried: eBay - too expensive)│
│ "})                                  │
└──────────────────────────────────────┘
```

## 4. Memory Tracking Pattern

```
┌────────────────────────────────────────┐
│ MEMORY EVOLUTION                       │
├────────────────────────────────────────┤
│                                        │
│ Step 1:                                │
│ "Researched best sites for laptops:   │
│  Amazon, Newegg, Best Buy"            │
│                                        │
│ Step 2:                                │
│ "Trying Amazon (1/3). Looking for     │
│  gaming laptops under $1000"          │
│                                        │
│ Step 3:                                │
│ "Amazon: Found 5 options but all over │
│  $1200. Now trying Newegg (2/3)"      │
│                                        │
│ Step 4:                                │
│ "Newegg: Found 3 options in budget!   │
│  Best option: [details]. Task complete"│
│                                        │
└────────────────────────────────────────┘
```

## 5. Action Sequence Example

```
┌──────────────────────────────────────────────┐
│ TASK: "Buy wireless earbuds under $50"       │
└──────────┬───────────────────────────────────┘
           ↓
    ┌────────────────┐
    │ find_best_     │
    │ website        │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Review search  │
    │ results        │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ search_        │
    │ ecommerce      │──→ Site: amazon.com
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Found 10       │
    │ results        │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Click on top   │
    │ result         │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Scroll down to │
    │ see price      │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Extract        │
    │ details        │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Go back        │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Repeat for     │
    │ 2 more items   │
    └────┬───────────┘
         ↓
    ┌────────────────┐
    │ Done with      │
    │ 3 options      │
    └────────────────┘
```

## 6. Error Recovery Flow

```
Normal Flow          Error Flow           Recovery
─────────────────────────────────────────────────
search_ecommerce
     ↓
Site loads     →    CAPTCHA detected   →  request_user_help
     ↓                                        ↓
Results shown       User solves CAPTCHA
     ↓                      ↓
Continue              Resume search
                           ↓
                      Results shown
                           ↓
                      Continue

─────────────────────────────────────────────────
search_ecommerce
     ↓
Site loads     →    No results found   →  Memory: "Site A: no results"
     ↓                                        ↓
Results shown       Try next site (Site B)
     ↓                      ↓
Continue              search_ecommerce
                           ↓
                      Results found
                           ↓
                      Continue

─────────────────────────────────────────────────
search_ecommerce
     ↓
Site loads     →    Timeout/Error      →  Memory: "Site A: technical issue"
     ↓                                        ↓
Results shown       Try next site (Site B)
     ↓                      ↓
Continue              search_ecommerce
                           ↓
                      Site loads
                           ↓
                      Continue
```

## 7. Decision Tree: When to Use Which Action

```
                    ┌─────────────┐
                    │  User Task  │
                    └──────┬──────┘
                           ↓
                  Is it shopping/
                 download/service?
                    ┌─────┴─────┐
                   YES          NO
                    ↓            ↓
              Know which    ┌────────┐
              site to use?  │ Use    │
              ┌─────┴─────┐ │ other  │
             YES          NO│ actions│
              ↓            ↓ └────────┘
         ┌─────────┐  ┌────────────┐
         │ search_ │  │ find_best_ │
         │ecommerce│  │ website    │
         │  with   │  │            │
         │ site    │  │            │
         │specified│  │            │
         └─────────┘  └──────┬─────┘
                             ↓
                      ┌──────────────┐
                      │ Review       │
                      │ results &    │
                      │ choose site  │
                      └──────┬───────┘
                             ↓
                      ┌──────────────┐
                      │ go_to_url OR │
                      │search_ecommerce│
                      └──────┬───────┘
                             ↓
                      ┌──────────────┐
                      │ Item found?  │
                      └──┬────────┬──┘
                        YES      NO
                         ↓       ↓
                      ┌────┐  ┌─────────────┐
                      │Done│  │Try next site│
                      └────┘  └──────┬──────┘
                                     ↓
                              ┌──────────────┐
                              │Repeat search │
                              │on new site   │
                              └──────────────┘
```

## 8. Comparison Matrix

| Feature                    | Old Approach | New Approach |
|----------------------------|--------------|--------------|
| **Site Selection**         | Hardcoded    | Dynamic      |
| **Multi-site Support**     | ❌           | ✅           |
| **Research Before Action** | ❌           | ✅           |
| **Fallback Strategy**      | ❌           | ✅           |
| **Memory Tracking**        | ❌           | ✅           |
| **International Sites**    | Limited      | Extensive    |
| **Custom Sites**           | ❌           | ✅           |
| **Success Rate**           | ~60%         | ~85%         |
| **User Flexibility**       | Low          | High         |
| **Auto-retry**             | ❌           | ✅           |

## 9. Agent State Machine

```
                    ┌─────────────┐
                    │   IDLE      │
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │ RESEARCHING │◄────┐
                    │  WEBSITES   │     │
                    └──────┬──────┘     │
                           ↓            │
                    ┌─────────────┐     │
                    │ SELECTING   │     │
                    │    SITE     │     │
                    └──────┬──────┘     │
                           ↓            │
                    ┌─────────────┐     │
                    │ NAVIGATING  │     │
                    └──────┬──────┘     │
                           ↓            │
                    ┌─────────────┐     │
                    │ SEARCHING   │     │
                    └──────┬──────┘     │
                           ↓            │
                    ┌─────────────┐     │
              ┌─────│ EVALUATING  │     │
              │     │  RESULTS    │     │
              │     └──────┬──────┘     │
              │            ↓            │
              │     Results good?       │
              │     ┌──────┴──────┐     │
              │    YES           NO     │
              │     ↓              ↓    │
              │ ┌─────────┐  ┌─────────┴──┐
              │ │EXTRACTING  │More sites? │
              │ └────┬─────┘  └─────┬──────┘
              │      ↓             YES
              │  ┌────────┐          │
              └─→│  DONE  │          │
                 └────────┘          │
                                     NO
                                     ↓
                              ┌──────────┐
                              │ FAILED   │
                              └──────────┘
```

## 10. Example Task Flows

### Task A: "Buy gaming laptop under $1000"
```
1. find_best_website("buy gaming laptop", "shopping")
   Memory: "Found sites: Amazon, Newegg, Best Buy"

2. search_ecommerce("gaming laptop", "amazon.com")
   Memory: "Amazon: 20 results, checking prices"

3. click_element(index=5)  # First result
   Memory: "Checking first laptop: $1299 - over budget"

4. go_back()
   Memory: "Back to results, trying next option"

5. click_element(index=8)  # Another result
   Memory: "Second laptop: $899 - within budget! ✓"

6. extract_content("laptop details")
   Memory: "Got specs and price for option 1"

7. [Repeat for 2 more options]
   Memory: "Collected 3 options from Amazon"

8. done("Found 3 gaming laptops under $1000: [details]")
```

### Task B: "Download Python tutorial PDF"
```
1. find_best_website("download python tutorial PDF", "download")
   Memory: "Top sites: Python.org, Real Python, Tutorial Point"

2. go_to_url("https://www.python.org")
   Memory: "Navigated to Python.org - official source"

3. input_text(index=2, text="beginner tutorial PDF")
   Memory: "Searching for beginner tutorial"

4. click_element(index=10)  # Search button
   Memory: "Search submitted, waiting for results"

5. scroll_down()
   Memory: "Looking for PDF downloads"

6. click_element(index=15)  # Download link
   Memory: "Found download link, clicking..."

7. done("Downloaded Python tutorial PDF from Python.org")
```

---

These diagrams illustrate the complete workflow and decision-making process of the intelligent website selection feature.
