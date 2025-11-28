import logging
import urllib.parse

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from browser_ai.agent.views import ActionResult
from browser_ai.browser.context import BrowserContext
from browser_ai.controller.views import (
    FindBestWebsiteAction,
    GoToUrlAction,
    NoParamsAction,
    SearchGoogleAction,
    SearchGoogleWithAiAction,
    SearchYouTubeAction,
)
from browser_ai.location_service import LocationDetector

logger = logging.getLogger(__name__)

async def search_google(params: SearchGoogleAction, browser: BrowserContext):
    page = await browser.get_current_page()
    # Try to avoid CAPTCHAs by not using shopping mode for general searches
    await page.goto(f"https://www.google.com/search?q={params.query}")
    await page.wait_for_load_state()
    msg = f'🔍  Searched for "{params.query}" in Google'
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def search_youtube(params: SearchYouTubeAction, browser: BrowserContext):
    page = await browser.get_current_page()
    search_query = params.query.replace(" ", "+")
    await page.goto(
        f"https://www.youtube.com/results?search_query={search_query}"
    )
    await page.wait_for_load_state()
    msg = f'🎥  Searched for "{params.query}" on YouTube'
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def search_google_with_ai(
    params: SearchGoogleWithAiAction,
    browser: BrowserContext,
    page_extraction_llm: BaseChatModel,
):
    # 1. Construct URL for Google's AI search mode
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(params.query)}&udm=50"

    # 2. Get current page index before opening new tab
    session = await browser.get_session()
    current_page = await browser.get_current_page()
    # Find the index of current page in the pages list
    original_page_id = None
    for i, page in enumerate(session.context.pages):
        if page == current_page:
            original_page_id = i
            break

    if original_page_id is None:
        original_page_id = 0  # Fallback to first tab

    # 3. Open the URL in a new tab
    await browser.create_new_tab(url)
    page = await browser.get_current_page()

    try:
        # 3. Wait for the AI response container to be visible
        container_selector = 'div[data-subtree="aimc"]'
        await page.wait_for_selector(
            container_selector, state="visible", timeout=20000
        )  # 20s timeout

        # 4. Extract the text content from the container
        container = await page.query_selector(container_selector)
        if not container:
            msg = "No AI Mode content found on the page."
            logger.warning(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

        ai_response_text = (await container.inner_text()).strip()

        if not ai_response_text:
            msg = "AI Mode container was found, but it was empty."
            logger.warning(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

        # 5. Use an LLM to process and summarize the extracted AI response
        prompt = (
            "Your task is to analyze the provided AI-generated search result and provide a concise summary or answer. "
            "Focus on the key information and present it clearly. AI-Generated Content: {content}"
        )
        template = PromptTemplate(input_variables=["content"], template=prompt)

        try:
            output = page_extraction_llm.invoke(
                template.format(content=ai_response_text)
            )
            summary = output.content
            msg = f'🤖 AI Search Summary for "{params.query}":\n\n{summary}'
            logger.info(
                f"Successfully processed AI search for '{params.query}'"
            )
            return ActionResult(extracted_content=msg, include_in_memory=True)
        except Exception as e:
            logger.error(f"Error processing AI content with LLM: {e}")
            # Fallback to returning the raw extracted text if LLM fails
            return ActionResult(
                extracted_content=f"Raw AI Response: {ai_response_text}",
                include_in_memory=True,
            )

    except Exception as e:
        error_msg = f"Failed to get AI-powered search results: {str(e)}"
        logger.error(error_msg)
        return ActionResult(error=error_msg, include_in_memory=True)
    finally:
        # 6. Clean up: close the new tab and switch back to the original one
        try:
            # Check if the page is still open before trying to close it
            if not page.is_closed():
                await page.close()
            # Switch back to original tab if it still exists
            session = await browser.get_session()
            if original_page_id < len(session.context.pages):
                await browser.switch_to_tab(original_page_id)
            logger.info("Closed AI search tab and returned to original page.")
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")
            # Try to at least switch back to the first tab as fallback
            try:
                await browser.switch_to_tab(0)
            except Exception:
                pass  # If even this fails, we'll just continue

async def find_best_website(
    params: FindBestWebsiteAction, browser: BrowserContext, location_detector: LocationDetector
):
    page = await browser.get_current_page()

    # Check if location is detected for shopping tasks
    location_context = ""
    if (
        params.category.lower() == "shopping"
        and location_detector.has_detected()
    ):
        location = location_detector.get_location()
        if location:
            location_context = f" in {location.country}"

    # Construct an intelligent search query to find the best websites
    if params.category.lower() == "shopping":
        search_query = (
            f"best website to buy {params.purpose} online{location_context}"
        )
    elif params.category.lower() == "download":
        search_query = f"best website to download {params.purpose}"
    elif params.category.lower() == "service":
        search_query = f"best website for {params.purpose}"
    else:
        search_query = f"best website for {params.purpose}"

    # Use Google to research the best websites
    encoded_query = search_query.replace(" ", "+")
    await page.goto(f"https://www.google.com/search?q={encoded_query}")
    await page.wait_for_load_state()

    # Include location-specific recommendations if available
    location_msg = ""
    if (
        params.category.lower() == "shopping"
        and location_detector.has_detected()
    ):
        location_msg = f"\n{location_detector.get_ecommerce_context()}"

    msg = (
        f"🔎  Researching best websites for: {params.purpose} (category: {params.category}). "
        "Review the search results to identify top websites, then navigate to the most appropriate one."
        f"{location_msg}"
    )
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def go_to_url(params: GoToUrlAction, browser: BrowserContext):
    page = await browser.get_current_page()
    await page.goto(params.url)
    await page.wait_for_load_state()
    msg = f"🔗  Navigated to {params.url}"
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def go_back(_: NoParamsAction, browser: BrowserContext):
    await browser.go_back()
    msg = "🔙  Navigated back"
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)
