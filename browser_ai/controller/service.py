import asyncio
import logging
from typing import Callable, Dict, Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel
from lmnr import Laminar, observe
from pydantic import BaseModel

from browser_ai.agent.views import ActionModel, ActionResult
from browser_ai.browser.context import BrowserContext
from browser_ai.controller.registry.service import Registry
from browser_ai.controller.views import (
    AskUserQuestionAction,
    ClickElementAction,
    DetectLocationAction,
    DoneAction,
    FindBestWebsiteAction,
    GoToUrlAction,
    InputTextAction,
    NoParamsAction,
    OpenTabAction,
    RequestUserHelpAction,
    ScrollAction,
    SearchEcommerceAction,
    SearchGoogleAction,
    SearchGoogleWithAiAction,
    SearchYouTubeAction,
    SendKeysAction,
    SwitchTabAction,
)
from browser_ai.location_service import LocationDetector
from browser_ai.utils import time_execution_async, time_execution_sync
import browser_ai.actions as actions

logger = logging.getLogger(__name__)


class Controller:
    def __init__(
        self,
        exclude_actions: list[str] = [],
        output_model: Optional[Type[BaseModel]] = None,
    ):
        self.exclude_actions = exclude_actions
        self.output_model = output_model
        self.registry = Registry(exclude_actions)
        self.location_detector = LocationDetector()  # Initialize location detector
        self._register_default_actions()

    def _register_default_actions(self):
        """Register all default browser actions"""

        if self.output_model is not None:

            @self.registry.action("Complete task", param_model=self.output_model)
            async def done(params: BaseModel):
                return await actions.done(params)

        else:

            @self.registry.action("Complete task", param_model=DoneAction)
            async def done(params: DoneAction):
                return await actions.done(params)

        # Basic Navigation Actions
        @self.registry.action(
            "Search the query in Google in the current tab. The query should be a search query like humans search in Google, concrete and not vague or super long. For shopping/buying tasks, consider using search_ecommerce instead to avoid CAPTCHAs. For research-oriented tasks, consider using search_google_with_ai for better results.",
            param_model=SearchGoogleAction,
        )
        async def search_google(params: SearchGoogleAction, browser: BrowserContext):
            return await actions.search_google(params, browser)

        @self.registry.action(
            "Search for videos on YouTube directly. Perfect for finding specific songs, music videos, tutorials, or any video content.",
            param_model=SearchYouTubeAction,
        )
        async def search_youtube(params: SearchYouTubeAction, browser: BrowserContext):
            return await actions.search_youtube(params, browser)

        @self.registry.action(
            (
                "Search Google using AI to generate a more effective search query based on your input, This helps in refining vague or complex queries to get better search results."
            ),
            param_model=SearchGoogleWithAiAction,
        )
        async def search_google_with_ai(
            params: SearchGoogleWithAiAction,
            browser: BrowserContext,
            page_extraction_llm: BaseChatModel,
        ):
            return await actions.search_google_with_ai(params, browser, page_extraction_llm)

        @self.registry.action(
            "Find the best website for a specific purpose (shopping, downloading, services, etc.). Use this FIRST before attempting to shop, download, or access specific content. Returns suggested websites to try.",
            param_model=FindBestWebsiteAction,
        )
        async def find_best_website(
            params: FindBestWebsiteAction, browser: BrowserContext
        ):
            return await actions.find_best_website(params, browser, self.location_detector)

        @self.registry.action(
            "Detect user location (country, currency, timezone) to provide personalized shopping experience. Use this BEFORE shopping tasks to get region-specific websites and currency information.",
            param_model=DetectLocationAction,
        )
        async def detect_location(
            params: DetectLocationAction, browser: BrowserContext
        ):
            return await actions.detect_location(params, browser, self.location_detector)

        @self.registry.action(
            "Search for products on e-commerce websites. You can specify any e-commerce site (amazon.com, ebay.com, daraz.lk, ikman.lk, glomark.lk, etc.) or leave blank to use location-based default. IMPORTANT: Use detect_location and find_best_website first for shopping tasks.",
            param_model=SearchEcommerceAction,
        )
        async def search_ecommerce(
            params: SearchEcommerceAction, browser: BrowserContext
        ):
            return await actions.search_ecommerce(params, browser, self.location_detector)

        @self.registry.action(
            "Navigate to URL in the current tab", param_model=GoToUrlAction
        )
        async def go_to_url(params: GoToUrlAction, browser: BrowserContext):
            return await actions.go_to_url(params, browser)

        @self.registry.action("Go back", param_model=NoParamsAction)
        async def go_back(_: NoParamsAction, browser: BrowserContext):
            return await actions.go_back(_, browser)

        # Element Interaction Actions
        @self.registry.action("Click element", param_model=ClickElementAction)
        async def click_element(params: ClickElementAction, browser: BrowserContext):
            return await actions.click_element(params, browser)

        @self.registry.action(
            "Input text into a input interactive element",
            param_model=InputTextAction,
        )
        async def input_text(params: InputTextAction, browser: BrowserContext):
            return await actions.input_text(params, browser)

        # Tab Management Actions
        @self.registry.action("Switch tab", param_model=SwitchTabAction)
        async def switch_tab(params: SwitchTabAction, browser: BrowserContext):
            return await actions.switch_tab(params, browser)

        @self.registry.action("Open url in new tab", param_model=OpenTabAction)
        async def open_tab(params: OpenTabAction, browser: BrowserContext):
            return await actions.open_tab(params, browser)

        # Content Actions
        @self.registry.action(
            "Extract page content to retrieve specific information from the page, e.g. all company names, a specifc description, all information about, links with companies in structured format or simply links",
        )
        async def extract_content(
            goal: str, browser: BrowserContext, page_extraction_llm: BaseChatModel
        ):
            return await actions.extract_content(goal, browser, page_extraction_llm)

        @self.registry.action(
            "Scroll down the page by pixel amount - if no amount is specified, scroll down one page",
            param_model=ScrollAction,
        )
        async def scroll_down(params: ScrollAction, browser: BrowserContext):
            return await actions.scroll_down(params, browser)

        # scroll up
        @self.registry.action(
            "Scroll up the page by pixel amount - if no amount is specified, scroll up one page",
            param_model=ScrollAction,
        )
        async def scroll_up(params: ScrollAction, browser: BrowserContext):
            return await actions.scroll_up(params, browser)

        # send keys
        @self.registry.action(
            "Send strings of special keys like Backspace, Insert, PageDown, Delete, Enter, Shortcuts such as `Control+o`, `Control+Shift+T` are supported as well. This gets used in keyboard.press. Be aware of different operating systems and their shortcuts",
            param_model=SendKeysAction,
        )
        async def send_keys(params: SendKeysAction, browser: BrowserContext):
            return await actions.send_keys(params, browser)

        @self.registry.action(
            description="Check if the current URL contains specific text (case-insensitive). Returns true/false. Useful for verifying navigation, email sent (check for 'sent' or 'sentitems'), form submission, etc.",
        )
        async def check_url_contains(text: str, browser: BrowserContext) -> ActionResult:
            return await actions.check_url_contains(text, browser)

        @self.registry.action(
            description="Wait for the URL to change or contain specific text. Useful for waiting for redirects after form submission, email sending, etc. Waits up to 10 seconds.",
        )
        async def wait_for_url_change(
            contains_text: str = "",
            timeout_seconds: int = 10,
            browser: BrowserContext = None
        ) -> ActionResult:
            return await actions.wait_for_url_change(contains_text, timeout_seconds, browser)

        @self.registry.action(
            description="Check if specific text exists on the current page. Returns true/false. Useful for verifying confirmation messages like 'Email sent', 'Message sent', 'Success', etc.",
        )
        async def check_page_contains_text(text: str, browser: BrowserContext) -> ActionResult:
            return await actions.check_page_contains_text(text, browser)

        @self.registry.action(
            description="If you dont find something which you want to interact with, scroll to it",
        )
        async def scroll_to_text(text: str, browser: BrowserContext):  # type: ignore
            return await actions.scroll_to_text(text, browser)

        @self.registry.action(
            description='Automatically scroll down to find specific text or element type. Useful when expected elements like "Buy Now", "Add to Cart" are not visible.',
        )
        async def auto_scroll_find(text: str, browser: BrowserContext, max_scrolls: int = 3):  # type: ignore
            return await actions.auto_scroll_find(text, browser, max_scrolls)

        @self.registry.action(
            description='Smart scroll to find common shopping/purchase elements like "Buy Now", "Add to Cart", "Checkout", etc. Useful for e-commerce sites.',
        )
        async def find_purchase_elements(browser: BrowserContext):  # type: ignore
            return await actions.find_purchase_elements(browser)

        @self.registry.action(
            description="Get all options from a native dropdown",
        )
        async def get_dropdown_options(
            index: int, browser: BrowserContext
        ) -> ActionResult:
            return await actions.get_dropdown_options(index, browser)

        @self.registry.action(
            description="Select dropdown option for interactive element index by the text of the option you want to select",
        )
        async def select_dropdown_option(
            index: int,
            text: str,
            browser: BrowserContext,
        ) -> ActionResult:
            return await actions.select_dropdown_option(index, text, browser)

        # User Assistance Actions
        @self.registry.action(
            "Request help from user for situations requiring human intervention: CAPTCHAs/verifications, login/signup forms, payment processing, sensitive data entry, or any complex authentication. Use this instead of attempting these tasks automatically to respect user privacy and security.",
            param_model=RequestUserHelpAction,
        )
        async def request_user_help(
            params: RequestUserHelpAction, browser: BrowserContext
        ):
            return await actions.request_user_help(params, browser)

        @self.registry.action(
            "Ask the user a clarifying question when you need more information to complete the task properly. Use this when: you are unsure about user preferences, need to choose between multiple options, or require specific details not provided in the original task. This enables interactive, conversational automation.",
            param_model=AskUserQuestionAction,
        )
        async def ask_user_question(
            params: AskUserQuestionAction, browser: BrowserContext
        ):
            return await actions.ask_user_question(params, browser)

    def action(self, description: str, **kwargs):
        """Decorator for registering custom actions

        @param description: Describe the LLM what the function does (better description == better function calling)
        """
        return self.registry.action(description, **kwargs)

    @observe(name="controller.multi_act")
    @time_execution_async("--multi-act")
    async def multi_act(
        self,
        actions: list[ActionModel],
        browser_context: BrowserContext,
        check_break_if_paused: Callable[[], bool],
        check_for_new_elements: bool = True,
        page_extraction_llm: Optional[BaseChatModel] = None,
        sensitive_data: Optional[Dict[str, str]] = None,
        available_file_paths: Optional[list[str]] = None,
    ) -> list[ActionResult]:
        """Execute multiple actions"""
        results = []

        session = await browser_context.get_session()
        cached_selector_map = session.cached_state.selector_map
        cached_path_hashes = set(
            e.hash.branch_path_hash for e in cached_selector_map.values()
        )

        check_break_if_paused()

        await browser_context.remove_highlights()

        for i, action in enumerate(actions):
            check_break_if_paused()

            if action.get_index() is not None and i != 0:
                new_state = await browser_context.get_state()
                new_path_hashes = set(
                    e.hash.branch_path_hash for e in new_state.selector_map.values()
                )
                if check_for_new_elements and not new_path_hashes.issubset(
                    cached_path_hashes
                ):
                    # next action requires index but there are new elements on the page
                    msg = f"Something new appeared after action {i} / {len(actions)}"
                    logger.info(msg)
                    results.append(
                        ActionResult(extracted_content=msg, include_in_memory=True)
                    )
                    break

            check_break_if_paused()

            results.append(
                await self.act(
                    action,
                    browser_context,
                    page_extraction_llm,
                    sensitive_data,
                    available_file_paths,
                )
            )

            logger.debug(f"Executed action {i + 1} / {len(actions)}")
            if results[-1].is_done or results[-1].error or i == len(actions) - 1:
                break

            await asyncio.sleep(browser_context.config.wait_between_actions)
            # hash all elements. if it is a subset of cached_state its fine - else break (new elements on page)

        return results

    @time_execution_sync("--act")
    async def act(
        self,
        action: ActionModel,
        browser_context: BrowserContext,
        page_extraction_llm: Optional[BaseChatModel] = None,
        sensitive_data: Optional[Dict[str, str]] = None,
        available_file_paths: Optional[list[str]] = None,
    ) -> ActionResult:
        """Execute an action"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    with Laminar.start_as_current_span(
                        name=action_name,
                        input={
                            "action": action_name,
                            "params": params,
                        },
                        span_type="TOOL",
                    ):
                        result = await self.registry.execute_action(
                            action_name,
                            params,
                            browser=browser_context,
                            page_extraction_llm=page_extraction_llm,
                            sensitive_data=sensitive_data,
                            available_file_paths=available_file_paths,
                        )

                        Laminar.set_span_output(result)

                    if isinstance(result, str):
                        return ActionResult(extracted_content=result)
                    elif isinstance(result, ActionResult):
                        return result
                    elif result is None:
                        return ActionResult()
                    else:
                        raise ValueError(
                            f"Invalid action result type: {type(result)} of {result}"
                        )
            return ActionResult()
        except Exception as e:
            raise e
