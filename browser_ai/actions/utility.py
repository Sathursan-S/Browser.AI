import logging

from pydantic import BaseModel

from browser_ai.agent.views import ActionResult
from browser_ai.browser.context import BrowserContext
from browser_ai.controller.views import (
    AskUserQuestionAction,
    DoneAction,
    OpenTabAction,
    RequestUserHelpAction,
    SwitchTabAction,
)

logger = logging.getLogger(__name__)

async def done(params: BaseModel | DoneAction):
    if isinstance(params, DoneAction):
        return ActionResult(is_done=True, extracted_content=params.text)
    return ActionResult(
        is_done=True, extracted_content=params.model_dump_json()
    )

async def switch_tab(params: SwitchTabAction, browser: BrowserContext):
    await browser.switch_to_tab(params.page_id)
    # Wait for tab to be ready
    page = await browser.get_current_page()
    await page.wait_for_load_state()
    msg = f"🔄  Switched to tab {params.page_id}"
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def open_tab(params: OpenTabAction, browser: BrowserContext):
    await browser.create_new_tab(params.url)
    msg = f"🔗  Opened new tab with {params.url}"
    logger.info(msg)
    return ActionResult(extracted_content=msg, include_in_memory=True)

async def request_user_help(
    params: RequestUserHelpAction, browser: BrowserContext
):
    msg = f"🙋‍♂️ Requesting user help: {params.message}"
    logger.warning(msg)
    logger.warning(f"Reason: {params.reason}")

    # Get current page info to help user understand context
    try:
        page = await browser.get_current_page()
        current_url = page.url
        logger.info(f"Current page: {current_url}")
    except Exception as e:
        current_url = "Unknown"

    # This will create a special result that signals the web interface to pause and request user input
    return ActionResult(
        extracted_content=f"{msg} - Please check the browser window at {current_url}",
        include_in_memory=True,
        requires_user_action=True,
        user_input_request={
            "type": "intervention",
            "reason": params.reason,
            "message": params.message,
            "url": current_url,
        },
    )

async def ask_user_question(
    params: AskUserQuestionAction, browser: BrowserContext
):
    msg = f"❓ Agent question: {params.question}"
    logger.info(msg)
    logger.info(f"Context: {params.context}")
    if params.options:
        logger.info(f'Suggested options: {", ".join(params.options)}')

    # This will create a special result that signals the web interface to pause and wait for user answer
    return ActionResult(
        extracted_content=f"{msg} (Context: {params.context})",
        include_in_memory=True,
        requires_user_action=True,
        user_input_request={
            "type": "question",
            "question": params.question,
            "context": params.context,
            "options": params.options,
        },
    )
