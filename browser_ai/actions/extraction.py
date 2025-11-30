import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from browser_ai.agent.views import ActionResult
from browser_ai.browser.context import BrowserContext
from browser_ai.controller.views import (
    DetectLocationAction,
    SearchEcommerceAction,
)
from browser_ai.location_service import LocationDetector

logger = logging.getLogger(__name__)

async def extract_content(
    goal: str, browser: BrowserContext, page_extraction_llm: BaseChatModel
):
    page = await browser.get_current_page()
    import markdownify

    content = markdownify.markdownify(await page.content())

    prompt = "Your task is to extract the content of the page. You will be given a page and a goal and you should extract all relevant information around this goal from the page. If the goal is vague, summarize the page. Respond in json format. Extraction goal: {goal}, Page: {page}"
    template = PromptTemplate(input_variables=["goal", "page"], template=prompt)
    try:
        output = page_extraction_llm.invoke(
            template.format(goal=goal, page=content)
        )
        msg = f"📄  Extracted from page\n: {output.content}\n"
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)
    except Exception as e:
        logger.debug(f"Error extracting content: {e}")
        msg = f"📄  Extracted from page\n: {content}\n"
        logger.info(msg)
        return ActionResult(extracted_content=msg)

async def detect_location(
    params: DetectLocationAction, browser: BrowserContext, location_detector: LocationDetector
):
    """Detect user's geographic location for personalized shopping"""
    location_info = await location_detector.detect_location_from_browser(
        browser
    )

    if location_info:
        context_msg = location_detector.get_full_context()
        msg = (
            f"📍 Location Detected!\n{context_msg}\n\n"
            "You can now use this information for personalized shopping and currency-aware searches."
        )
        logger.info(f"Location detected: {location_info.country}")
    else:
        msg = "⚠️ Could not detect location. Defaulting to United States (USD)."
        logger.warning("Location detection failed, using US default")

    return ActionResult(extracted_content=msg, include_in_memory=True)

async def search_ecommerce(
    params: SearchEcommerceAction, browser: BrowserContext, location_detector: LocationDetector
):
    page = await browser.get_current_page()
    search_query = params.query.replace(" ", "+")

    # If site is specified, use it; otherwise use location-based default
    if params.site:
        site = params.site.lower()

        # Build search URL based on known site patterns
        if "daraz.lk" in site or site == "daraz":
            search_url = f"https://www.daraz.lk/catalog/?q={search_query}"
        elif "ikman.lk" in site or site == "ikman":
            search_url = f"https://ikman.lk/en/ads?query={search_query}"
        elif "glomark.lk" in site or site == "glomark":
            search_url = f"https://glomark.lk/search?q={search_query}"
        elif "amazon.com" in site or site == "amazon":
            search_url = f"https://www.amazon.com/s?k={search_query}"
        elif "ebay.com" in site or site == "ebay":
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={search_query}"
        elif "alibaba.com" in site or site == "alibaba":
            search_url = f"https://www.alibaba.com/trade/search?SearchText={search_query}"
        elif "aliexpress.com" in site or site == "aliexpress":
            search_url = f"https://www.aliexpress.com/wholesale?SearchText={search_query}"
        else:
            # For unknown sites, try to construct a generic search URL
            # Remove common TLDs and use as base domain
            base_site = site.replace("www.", "").split("/")[0]
            search_url = f"https://{base_site}/search?q={search_query}"
    else:
        # Use location-based default site
        if (
            location_detector.has_detected()
            and location_detector.get_location()
        ):
            location = location_detector.get_location()
            # Use the first preferred site for this location
            preferred_site = (
                location.preferred_ecommerce_sites[0]
                if location.preferred_ecommerce_sites
                else "amazon.com"
            )

            # Build URL for preferred site
            if "daraz" in preferred_site:
                search_url = (
                    f"https://{preferred_site}/catalog/?q={search_query}"
                )
                site = preferred_site
            elif "amazon" in preferred_site:
                search_url = f"https://{preferred_site}/s?k={search_query}"
                site = preferred_site
            elif "ebay" in preferred_site:
                search_url = (
                    f"https://{preferred_site}/sch/i.html?_nkw={search_query}"
                )
                site = preferred_site
            elif "lazada" in preferred_site:
                search_url = (
                    f"https://{preferred_site}/catalog/?q={search_query}"
                )
                site = preferred_site
            elif "shopee" in preferred_site:
                search_url = (
                    f"https://{preferred_site}/search?keyword={search_query}"
                )
                site = preferred_site
            else:
                # Generic fallback
                search_url = f"https://{preferred_site}/search?q={search_query}"
                site = preferred_site
        else:
            # Absolute fallback - use Amazon
            search_url = f"https://www.amazon.com/s?k={search_query}"
            site = "amazon.com"

    await page.goto(search_url)
    await page.wait_for_load_state()

    # Add currency context if location is detected
    currency_info = ""
    if (
        location_detector.has_detected()
        and location_detector.get_location()
    ):
        currency_info = f" ({location_detector.get_currency_context()})"

    msg = f'🛒  Searched for "{params.query}" on {site}{currency_info}'
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)
