import asyncio
import json
import logging

from browser_ai.agent.views import ActionResult
from browser_ai.browser.context import BrowserContext
from browser_ai.controller.views import (
    ClickElementAction,
    InputTextAction,
    ScrollAction,
    SendKeysAction,
)

logger = logging.getLogger(__name__)

async def click_element(params: ClickElementAction, browser: BrowserContext):
    session = await browser.get_session()
    state = session.cached_state

    if params.index not in state.selector_map:
        raise Exception(
            f"Element with index {params.index} does not exist - retry or use alternative actions"
        )

    element_node = state.selector_map[params.index]
    initial_pages = len(session.context.pages)

    # if element has file uploader then dont click
    if await browser.is_file_uploader(element_node):
        msg = (
            f"Index {params.index} - has an element which opens file upload dialog. "
            "To upload files please use a specific function to upload files "
        )
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    msg = None

    try:
        download_path = await browser._click_element_node(element_node)
        if download_path:
            msg = f"💾  Downloaded file to {download_path}"
        else:
            msg = (
                f"🖱️  Clicked button with index {params.index}: "
                f"{element_node.get_all_text_till_next_clickable_element(max_depth=2)}"
            )

        logger.info(msg)
        logger.debug(f"Element xpath: {element_node.xpath}")
        if len(session.context.pages) > initial_pages:
            new_tab_msg = "New tab opened - switching to it"
            msg += f" - {new_tab_msg}"
            logger.info(new_tab_msg)
            await browser.switch_to_tab(-1)
        return ActionResult(extracted_content=msg, include_in_memory=True)
    except Exception as e:
        logger.warning(
            f"Element not clickable with index {params.index} - most likely the page changed"
        )
        return ActionResult(error=str(e))

async def input_text(params: InputTextAction, browser: BrowserContext):
    session = await browser.get_session()
    state = session.cached_state

    if params.index not in state.selector_map:
        raise Exception(
            f"Element index {params.index} does not exist - retry or use alternative actions"
        )

    element_node = state.selector_map[params.index]
    await browser._input_text_element_node(element_node, params.text)
    msg = f"⌨️  Input {params.text} into index {params.index}"
    logger.info(msg)
    logger.debug(f"Element xpath: {element_node.xpath}")
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def scroll_down(params: ScrollAction, browser: BrowserContext):
    page = await browser.get_current_page()
    if params.amount is not None:
        await page.evaluate(f"window.scrollBy(0, {params.amount});")
    else:
        await page.evaluate("window.scrollBy(0, window.innerHeight);")

    amount = (
        f"{params.amount} pixels" if params.amount is not None else "one page"
    )
    msg = f"🔍  Scrolled down the page by {amount}"
    logger.info(msg)
    return ActionResult(
        extracted_content=msg,
        include_in_memory=True,
    )

async def scroll_up(params: ScrollAction, browser: BrowserContext):
    page = await browser.get_current_page()
    if params.amount is not None:
        await page.evaluate(f"window.scrollBy(0, -{params.amount});")
    else:
        await page.evaluate("window.scrollBy(0, -window.innerHeight);")

    amount = (
        f"{params.amount} pixels" if params.amount is not None else "one page"
    )
    msg = f"🔍  Scrolled up the page by {amount}"
    logger.info(msg)
    return ActionResult(
        extracted_content=msg,
        include_in_memory=True,
    )

async def send_keys(params: SendKeysAction, browser: BrowserContext):
    page = await browser.get_current_page()

    await page.keyboard.press(params.keys)
    msg = f"⌨️  Sent keys: {params.keys}"
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def check_url_contains(text: str, browser: BrowserContext) -> ActionResult:
    """Check if current URL contains specific text"""
    page = await browser.get_current_page()
    current_url = page.url
    contains = text.lower() in current_url.lower()

    if contains:
        msg = f"✓ URL contains '{text}': {current_url}"
    else:
        msg = f"✗ URL does NOT contain '{text}': {current_url}"

    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def wait_for_url_change(
    contains_text: str = "",
    timeout_seconds: int = 10,
    browser: BrowserContext = None
) -> ActionResult:
    """Wait for URL to change or contain specific text"""
    page = await browser.get_current_page()
    initial_url = page.url

    try:
        if contains_text:
            # Wait for URL to contain specific text
            await page.wait_for_url(
                lambda url: contains_text.lower() in url.lower(),
                timeout=timeout_seconds * 1000
            )
            msg = f"✓ URL now contains '{contains_text}': {page.url}"
        else:
            # Wait for any URL change
            await page.wait_for_url(
                lambda url: url != initial_url,
                timeout=timeout_seconds * 1000
            )
            msg = f"✓ URL changed from {initial_url} to {page.url}"

        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    except Exception:
        msg = f"Timeout: URL did not change as expected. Current URL: {page.url}"
        logger.warning(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

async def check_page_contains_text(text: str, browser: BrowserContext) -> ActionResult:
    """Check if page contains specific text (case-insensitive)"""
    page = await browser.get_current_page()

    try:
        # Try to find the text using different methods
        text_found = False

        # Method 1: Check with Playwright's get_by_text
        try:
            locator = page.get_by_text(text, exact=False)
            if await locator.count() > 0:
                text_found = True
        except:
            pass

        # Method 2: Check page content if not found
        if not text_found:
            page_content = await page.content()
            if text.lower() in page_content.lower():
                text_found = True

        if text_found:
            msg = f"✓ Page contains text: '{text}'"
        else:
            msg = f"✗ Page does NOT contain text: '{text}'"

        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    except Exception as e:
        msg = f"Error checking for text '{text}': {str(e)}"
        logger.error(msg)
        return ActionResult(error=msg, include_in_memory=True)

async def scroll_to_text(text: str, browser: BrowserContext):  # type: ignore
    page = await browser.get_current_page()
    try:
        # Try different locator strategies
        locators = [
            page.get_by_text(text, exact=False),
            page.locator(f"text={text}"),
            page.locator(f"//*[contains(text(), '{text}')]"),
        ]

        for locator in locators:
            try:
                # First check if element exists and is visible
                if (
                    await locator.count() > 0
                    and await locator.first.is_visible()
                ):
                    await locator.first.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)  # Wait for scroll to complete
                    msg = f"🔍  Scrolled to text: {text}"
                    logger.info(msg)
                    return ActionResult(
                        extracted_content=msg, include_in_memory=True
                    )
            except Exception as e:
                logger.debug(f"Locator attempt failed: {str(e)}")
                continue

        msg = f"Text '{text}' not found or not visible on page"
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    except Exception as e:
        msg = f"Failed to scroll to text '{text}': {str(e)}"
        logger.error(msg)
        return ActionResult(error=msg, include_in_memory=True)

async def auto_scroll_find(text: str, browser: BrowserContext, max_scrolls: int = 3):  # type: ignore
    page = await browser.get_current_page()

    for scroll_attempt in range(max_scrolls):
        try:
            # Check if the text exists on current view
            if await page.get_by_text(text, exact=False).count() > 0:
                msg = f'🔍  Found "{text}" after {scroll_attempt} scrolls'
                logger.info(msg)
                return ActionResult(
                    extracted_content=msg, include_in_memory=True
                )

            # Scroll down and wait a bit for content to load
            await page.evaluate("window.scrollBy(0, window.innerHeight);")
            await asyncio.sleep(1)

        except Exception as e:
            logger.debug(
                f"Auto scroll attempt {scroll_attempt} failed: {str(e)}"
            )
            continue

    msg = f'🔍  Could not find "{text}" after {max_scrolls} scroll attempts'
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def find_purchase_elements(browser: BrowserContext):  # type: ignore
    page = await browser.get_current_page()

    # Common purchase-related texts to look for
    purchase_texts = [
        "Buy Now",
        "Add to Cart",
        "Add to Bag",
        "Purchase",
        "Order Now",
        "Checkout",
        "Proceed to Checkout",
        "Continue",
        "Place Order",
        "Add to Basket",
        "Buy",
        "Shop Now",
        "Get Now",
    ]

    # Scroll down up to 5 times looking for purchase elements
    for scroll_attempt in range(5):
        try:
            # Check for any purchase-related text
            found_elements = []
            for text in purchase_texts:
                if await page.get_by_text(text, exact=False).count() > 0:
                    found_elements.append(text)

            if found_elements:
                msg = f'🛒  Found purchase elements after {scroll_attempt} scrolls: {", ".join(found_elements)}'
                logger.info(msg)
                return ActionResult(
                    extracted_content=msg, include_in_memory=True
                )

            # Scroll down and wait for content to load
            await page.evaluate("window.scrollBy(0, window.innerHeight);")
            await asyncio.sleep(1.5)

        except Exception as e:
            logger.debug(
                f"Purchase element search attempt {scroll_attempt} failed: {str(e)}"
            )
            continue

    msg = "🛒  Could not find purchase elements after 5 scroll attempts"
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def get_dropdown_options(
    index: int, browser: BrowserContext
) -> ActionResult:
    """Get all options from a native dropdown"""
    page = await browser.get_current_page()
    selector_map = await browser.get_selector_map()
    dom_element = selector_map[index]

    try:
        # Frame-aware approach since we know it works
        all_options = []
        frame_index = 0

        for frame in page.frames:
            try:
                options = await frame.evaluate(
                    """
                    (xpath) => {
                        const select = document.evaluate(xpath, document, null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (!select) return null;

                        return {
                            options: Array.from(select.options).map(opt => ({
                                text: opt.text, //do not trim, because we are doing exact match in select_dropdown_option
                                value: opt.value,
                                index: opt.index
                            })),
                            id: select.id,
                            name: select.name
                        };
                    }
                """,
                    dom_element.xpath,
                )

                if options:
                    logger.debug(f"Found dropdown in frame {frame_index}")
                    logger.debug(
                        f'Dropdown ID: {options["id"]}, Name: {options["name"]}'
                    )

                    formatted_options = []
                    for opt in options["options"]:
                        # encoding ensures AI uses the exact string in select_dropdown_option
                        encoded_text = json.dumps(opt["text"])
                        formatted_options.append(
                            f'{opt["index"]}: text={encoded_text}'
                        )

                    all_options.extend(formatted_options)

            except Exception as frame_e:
                logger.debug(
                    f"Frame {frame_index} evaluation failed: {str(frame_e)}"
                )

            frame_index += 1

        if all_options:
            msg = "\n".join(all_options)
            msg += "\nUse the exact text string in select_dropdown_option"
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        else:
            msg = "No options found in any frame for dropdown"
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

    except Exception as e:
        logger.error(f"Failed to get dropdown options: {str(e)}")
        msg = f"Error getting options: {str(e)}"
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

async def select_dropdown_option(
    index: int,
    text: str,
    browser: BrowserContext,
) -> ActionResult:
    """Select dropdown option by the text of the option you want to select"""
    page = await browser.get_current_page()
    selector_map = await browser.get_selector_map()
    dom_element = selector_map[index]

    # Validate that we're working with a select element
    if dom_element.tag_name != "select":
        logger.error(
            f"Element is not a select! Tag: {dom_element.tag_name}, Attributes: {dom_element.attributes}"
        )
        msg = f"Cannot select option: Element with index {index} is a {dom_element.tag_name}, not a select"
        return ActionResult(extracted_content=msg, include_in_memory=True)

    logger.debug(
        f"Attempting to select '{text}' using xpath: {dom_element.xpath}"
    )
    logger.debug(f"Element attributes: {dom_element.attributes}")
    logger.debug(f"Element tag: {dom_element.tag_name}")

    xpath = "//" + dom_element.xpath

    try:
        frame_index = 0
        for frame in page.frames:
            try:
                logger.debug(f"Trying frame {frame_index} URL: {frame.url}")

                # First verify we can find the dropdown in this frame
                find_dropdown_js = """
                    (xpath) => {
                        try {
                            const select = document.evaluate(xpath, document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (!select) return null;
                            if (select.tagName.toLowerCase() !== 'select') {
                                return {
                                    error: `Found element but it's a ${select.tagName}, not a SELECT`,
                                    found: false
                                };
                            }
                            return {
                                id: select.id,
                                name: select.name,
                                found: true,
                                tagName: select.tagName,
                                optionCount: select.options.length,
                                currentValue: select.value,
                                availableOptions: Array.from(select.options).map(o => o.text.trim())
                            };
                        } catch (e) {
                            return {error: e.toString(), found: false};
                        }
                    }
                """

                dropdown_info = await frame.evaluate(
                    find_dropdown_js, dom_element.xpath
                )

                if dropdown_info:
                    if not dropdown_info.get("found"):
                        logger.error(
                            f'Frame {frame_index} error: {dropdown_info.get("error")}'
                        )
                        continue

                    logger.debug(
                        f"Found dropdown in frame {frame_index}: {dropdown_info}"
                    )

                    # "label" because we are selecting by text
                    # nth(0) to disable error thrown by strict mode
                    # timeout=1000 because we are already waiting for all network events, therefore ideally we don't need to wait a lot here (default 30s)
                    selected_option_values = (
                        await frame.locator("//" + dom_element.xpath)
                        .nth(0)
                        .select_option(label=text, timeout=1000)
                    )

                    msg = f"selected option {text} with value {selected_option_values}"
                    logger.info(msg + f" in frame {frame_index}")

                    return ActionResult(
                        extracted_content=msg, include_in_memory=True
                    )

            except Exception as frame_e:
                logger.error(
                    f"Frame {frame_index} attempt failed: {str(frame_e)}"
                )
                logger.error(f"Frame type: {type(frame)}")
                logger.error(f"Frame URL: {frame.url}")

            frame_index += 1

        msg = f"Could not select option '{text}' in any frame"
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True)

    except Exception as e:
        msg = f"Selection failed: {str(e)}"
        logger.error(msg)
        return ActionResult(error=msg, include_in_memory=True)
