import asyncio
import json
import logging
import urllib.parse
from typing import Callable, Dict, Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
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

			@self.registry.action('Complete task', param_model=self.output_model)
			async def done(params: BaseModel):
				return ActionResult(is_done=True, extracted_content=params.model_dump_json())
		else:

			@self.registry.action('Complete task', param_model=DoneAction)
			async def done(params: DoneAction):
				return ActionResult(is_done=True, extracted_content=params.text)

		# Basic Navigation Actions
		@self.registry.action(
			'Search the query in Google in the current tab. The query should be a search query like humans search in Google, concrete and not vague or super long. For shopping/buying tasks, consider using search_ecommerce instead to avoid CAPTCHAs.',
			param_model=SearchGoogleAction,
		)
		async def search_google(params: SearchGoogleAction, browser: BrowserContext):
			page = await browser.get_current_page()
			# Try to avoid CAPTCHAs by not using shopping mode for general searches
			await page.goto(f'https://www.google.com/search?q={params.query}')
			await page.wait_for_load_state()
			msg = f'🔍  Searched for "{params.query}" in Google'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			'Search for videos on YouTube directly. Perfect for finding specific songs, music videos, tutorials, or any video content.',
			param_model=SearchYouTubeAction,
		)
		async def search_youtube(params: SearchYouTubeAction, browser: BrowserContext):
			page = await browser.get_current_page()
			search_query = params.query.replace(' ', '+')
			await page.goto(f'https://www.youtube.com/results?search_query={search_query}')
			await page.wait_for_load_state()
			msg = f'🎥  Searched for "{params.query}" on YouTube'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			(
				'Search Google using AI to generate a more effective search query based on your input. '
				'This helps in refining vague or complex queries to get better search results.'
			),
			param_model=SearchGoogleWithAiAction,
		)
		async def search_google_with_ai(
			params: SearchGoogleWithAiAction, browser: BrowserContext, page_extraction_llm: BaseChatModel
		):
			# 1. Construct URL for Google's AI search mode
			url = f"https://www.google.com/search?q={urllib.parse.quote_plus(params.query)}&udm=50"

			# 2. Open the URL in a new tab
			original_page_id = (await browser.get_current_page()).page_id
			await browser.create_new_tab(url)
			page = await browser.get_current_page()

			try:
				# 3. Wait for the AI response container to be visible
				container_selector = 'div[data-subtree="aimc"]'
				await page.wait_for_selector(container_selector, state='visible', timeout=20000)  # 20s timeout

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
					'Your task is to analyze the provided AI-generated search result and provide a concise summary or answer. '
					'Focus on the key information and present it clearly. AI-Generated Content: {content}'
				)
				template = PromptTemplate(input_variables=['content'], template=prompt)

				try:
					output = page_extraction_llm.invoke(template.format(content=ai_response_text))
					summary = output.content
					msg = f'🤖 AI Search Summary for "{params.query}":\n\n{summary}'
					logger.info(f"Successfully processed AI search for '{params.query}'")
					return ActionResult(extracted_content=msg, include_in_memory=True)
				except Exception as e:
					logger.error(f'Error processing AI content with LLM: {e}')
					# Fallback to returning the raw extracted text if LLM fails
					return ActionResult(extracted_content=f"Raw AI Response: {ai_response_text}", include_in_memory=True)

			except Exception as e:
				error_msg = f"Failed to get AI-powered search results: {str(e)}"
				logger.error(error_msg)
				return ActionResult(error=error_msg, include_in_memory=True)
			finally:
				# 6. Clean up: close the new tab and switch back to the original one
				await page.close()
				await browser.switch_to_tab(original_page_id)
				logger.info("Closed AI search tab and returned to original page.")

		@self.registry.action(
			'Find the best website for a specific purpose (shopping, downloading, services, etc.). Use this FIRST before attempting to shop, download, or access specific content. Returns suggested websites to try.',
			param_model=FindBestWebsiteAction,
		)
		async def find_best_website(params: FindBestWebsiteAction, browser: BrowserContext):
			page = await browser.get_current_page()
			
			# Check if location is detected for shopping tasks
			location_context = ""
			if params.category.lower() == 'shopping' and self.location_detector.has_detected():
				location = self.location_detector.get_location()
				if location:
					location_context = f" in {location.country}"
			
			# Construct an intelligent search query to find the best websites
			if params.category.lower() == 'shopping':
				search_query = f'best website to buy {params.purpose} online{location_context}'
			elif params.category.lower() == 'download':
				search_query = f'best website to download {params.purpose}'
			elif params.category.lower() == 'service':
				search_query = f'best website for {params.purpose}'
			else:
				search_query = f'best website for {params.purpose}'
			
			# Use Google to research the best websites
			encoded_query = search_query.replace(' ', '+')
			await page.goto(f'https://www.google.com/search?q={encoded_query}')
			await page.wait_for_load_state()
			
			# Include location-specific recommendations if available
			location_msg = ""
			if params.category.lower() == 'shopping' and self.location_detector.has_detected():
				location_msg = f"\n{self.location_detector.get_ecommerce_context()}"
			
			msg = (
				f'🔎  Researching best websites for: {params.purpose} (category: {params.category}). '
				'Review the search results to identify top websites, then navigate to the most appropriate one.'
				f'{location_msg}'
			)
			logger.info(msg)
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True
			)

		@self.registry.action(
			'Detect user location (country, currency, timezone) to provide personalized shopping experience. Use this BEFORE shopping tasks to get region-specific websites and currency information.',
			param_model=DetectLocationAction,
		)
		async def detect_location(params: DetectLocationAction, browser: BrowserContext):
			"""Detect user's geographic location for personalized shopping"""
			location_info = await self.location_detector.detect_location_from_browser(browser)
			
			if location_info:
				context_msg = self.location_detector.get_full_context()
				msg = (
					f'📍 Location Detected!\n{context_msg}\n\n'
					'You can now use this information for personalized shopping and currency-aware searches.'
				)
				logger.info(f"Location detected: {location_info.country}")
			else:
				msg = '⚠️ Could not detect location. Defaulting to United States (USD).'
				logger.warning("Location detection failed, using US default")
			
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True
			)

		@self.registry.action(
			'Search for products on e-commerce websites. You can specify any e-commerce site (amazon.com, ebay.com, daraz.lk, ikman.lk, glomark.lk, etc.) or leave blank to use location-based default. IMPORTANT: Use detect_location and find_best_website first for shopping tasks.',
			param_model=SearchEcommerceAction,
		)
		async def search_ecommerce(params: SearchEcommerceAction, browser: BrowserContext):
			page = await browser.get_current_page()
			search_query = params.query.replace(' ', '+')
			
			# If site is specified, use it; otherwise use location-based default
			if params.site:
				site = params.site.lower()
				
				# Build search URL based on known site patterns
				if 'daraz.lk' in site or site == 'daraz':
					search_url = f'https://www.daraz.lk/catalog/?q={search_query}'
				elif 'ikman.lk' in site or site == 'ikman':
					search_url = f'https://ikman.lk/en/ads?query={search_query}'
				elif 'glomark.lk' in site or site == 'glomark':
					search_url = f'https://glomark.lk/search?q={search_query}'
				elif 'amazon.com' in site or site == 'amazon':
					search_url = f'https://www.amazon.com/s?k={search_query}'
				elif 'ebay.com' in site or site == 'ebay':
					search_url = f'https://www.ebay.com/sch/i.html?_nkw={search_query}'
				elif 'alibaba.com' in site or site == 'alibaba':
					search_url = f'https://www.alibaba.com/trade/search?SearchText={search_query}'
				elif 'aliexpress.com' in site or site == 'aliexpress':
					search_url = f'https://www.aliexpress.com/wholesale?SearchText={search_query}'
				else:
					# For unknown sites, try to construct a generic search URL
					# Remove common TLDs and use as base domain
					base_site = site.replace('www.', '').split('/')[0]
					search_url = f'https://{base_site}/search?q={search_query}'
			else:
				# Use location-based default site
				if self.location_detector.has_detected() and self.location_detector.get_location():
					location = self.location_detector.get_location()
					# Use the first preferred site for this location
					preferred_site = location.preferred_ecommerce_sites[0] if location.preferred_ecommerce_sites else 'amazon.com'
					
					# Build URL for preferred site
					if 'daraz' in preferred_site:
						search_url = f'https://{preferred_site}/catalog/?q={search_query}'
						site = preferred_site
					elif 'amazon' in preferred_site:
						search_url = f'https://{preferred_site}/s?k={search_query}'
						site = preferred_site
					elif 'ebay' in preferred_site:
						search_url = f'https://{preferred_site}/sch/i.html?_nkw={search_query}'
						site = preferred_site
					elif 'lazada' in preferred_site:
						search_url = f'https://{preferred_site}/catalog/?q={search_query}'
						site = preferred_site
					elif 'shopee' in preferred_site:
						search_url = f'https://{preferred_site}/search?keyword={search_query}'
						site = preferred_site
					else:
						# Generic fallback
						search_url = f'https://{preferred_site}/search?q={search_query}'
						site = preferred_site
				else:
					# Absolute fallback - use Amazon
					search_url = f'https://www.amazon.com/s?k={search_query}'
					site = 'amazon.com'
			
			await page.goto(search_url)
			await page.wait_for_load_state()
			
			# Add currency context if location is detected
			currency_info = ""
			if self.location_detector.has_detected() and self.location_detector.get_location():
				currency_info = f" ({self.location_detector.get_currency_context()})"
			
			msg = f'🛒  Searched for "{params.query}" on {site}{currency_info}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('Navigate to URL in the current tab', param_model=GoToUrlAction)
		async def go_to_url(params: GoToUrlAction, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.goto(params.url)
			await page.wait_for_load_state()
			msg = f'🔗  Navigated to {params.url}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('Go back', param_model=NoParamsAction)
		async def go_back(_: NoParamsAction, browser: BrowserContext):
			await browser.go_back()
			msg = '🔙  Navigated back'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Element Interaction Actions
		@self.registry.action('Click element', param_model=ClickElementAction)
		async def click_element(params: ClickElementAction, browser: BrowserContext):
			session = await browser.get_session()
			state = session.cached_state

			if params.index not in state.selector_map:
				raise Exception(f'Element with index {params.index} does not exist - retry or use alternative actions')

			element_node = state.selector_map[params.index]
			initial_pages = len(session.context.pages)

			# if element has file uploader then dont click
			if await browser.is_file_uploader(element_node):
				msg = (
					f'Index {params.index} - has an element which opens file upload dialog. '
					'To upload files please use a specific function to upload files '
				)
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			msg = None

			try:
				download_path = await browser._click_element_node(element_node)
				if download_path:
					msg = f'💾  Downloaded file to {download_path}'
				else:
					msg = (
						f'🖱️  Clicked button with index {params.index}: '
						f'{element_node.get_all_text_till_next_clickable_element(max_depth=2)}'
					)

				logger.info(msg)
				logger.debug(f'Element xpath: {element_node.xpath}')
				if len(session.context.pages) > initial_pages:
					new_tab_msg = 'New tab opened - switching to it'
					msg += f' - {new_tab_msg}'
					logger.info(new_tab_msg)
					await browser.switch_to_tab(-1)
				return ActionResult(extracted_content=msg, include_in_memory=True)
			except Exception as e:
				logger.warning(f'Element not clickable with index {params.index} - most likely the page changed')
				return ActionResult(error=str(e))

		@self.registry.action(
			'Input text into a input interactive element',
			param_model=InputTextAction,
		)
		async def input_text(params: InputTextAction, browser: BrowserContext):
			session = await browser.get_session()
			state = session.cached_state

			if params.index not in state.selector_map:
				raise Exception(f'Element index {params.index} does not exist - retry or use alternative actions')

			element_node = state.selector_map[params.index]
			await browser._input_text_element_node(element_node, params.text)
			msg = f'⌨️  Input {params.text} into index {params.index}'
			logger.info(msg)
			logger.debug(f'Element xpath: {element_node.xpath}')
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Tab Management Actions
		@self.registry.action('Switch tab', param_model=SwitchTabAction)
		async def switch_tab(params: SwitchTabAction, browser: BrowserContext):
			await browser.switch_to_tab(params.page_id)
			# Wait for tab to be ready
			page = await browser.get_current_page()
			await page.wait_for_load_state()
			msg = f'🔄  Switched to tab {params.page_id}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('Open url in new tab', param_model=OpenTabAction)
		async def open_tab(params: OpenTabAction, browser: BrowserContext):
			await browser.create_new_tab(params.url)
			msg = f'🔗  Opened new tab with {params.url}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Content Actions
		@self.registry.action(
			'Extract page content to retrieve specific information from the page, e.g. all company names, a specifc description, all information about, links with companies in structured format or simply links',
		)
		async def extract_content(goal: str, browser: BrowserContext, page_extraction_llm: BaseChatModel):
			page = await browser.get_current_page()
			import markdownify

			content = markdownify.markdownify(await page.content())

			prompt = 'Your task is to extract the content of the page. You will be given a page and a goal and you should extract all relevant information around this goal from the page. If the goal is vague, summarize the page. Respond in json format. Extraction goal: {goal}, Page: {page}'
			template = PromptTemplate(input_variables=['goal', 'page'], template=prompt)
			try:
				output = page_extraction_llm.invoke(template.format(goal=goal, page=content))
				msg = f'📄  Extracted from page\n: {output.content}\n'
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)
			except Exception as e:
				logger.debug(f'Error extracting content: {e}')
				msg = f'📄  Extracted from page\n: {content}\n'
				logger.info(msg)
				return ActionResult(extracted_content=msg)

		@self.registry.action(
			'Scroll down the page by pixel amount - if no amount is specified, scroll down one page',
			param_model=ScrollAction,
		)
		async def scroll_down(params: ScrollAction, browser: BrowserContext):
			page = await browser.get_current_page()
			if params.amount is not None:
				await page.evaluate(f'window.scrollBy(0, {params.amount});')
			else:
				await page.evaluate('window.scrollBy(0, window.innerHeight);')

			amount = f'{params.amount} pixels' if params.amount is not None else 'one page'
			msg = f'🔍  Scrolled down the page by {amount}'
			logger.info(msg)
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True,
			)

		# scroll up
		@self.registry.action(
			'Scroll up the page by pixel amount - if no amount is specified, scroll up one page',
			param_model=ScrollAction,
		)
		async def scroll_up(params: ScrollAction, browser: BrowserContext):
			page = await browser.get_current_page()
			if params.amount is not None:
				await page.evaluate(f'window.scrollBy(0, -{params.amount});')
			else:
				await page.evaluate('window.scrollBy(0, -window.innerHeight);')

			amount = f'{params.amount} pixels' if params.amount is not None else 'one page'
			msg = f'🔍  Scrolled up the page by {amount}'
			logger.info(msg)
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True,
			)

		# send keys
		@self.registry.action(
			'Send strings of special keys like Backspace, Insert, PageDown, Delete, Enter, Shortcuts such as `Control+o`, `Control+Shift+T` are supported as well. This gets used in keyboard.press. Be aware of different operating systems and their shortcuts',
			param_model=SendKeysAction,
		)
		async def send_keys(params: SendKeysAction, browser: BrowserContext):
			page = await browser.get_current_page()

			await page.keyboard.press(params.keys)
			msg = f'⌨️  Sent keys: {params.keys}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='If you dont find something which you want to interact with, scroll to it',
		)
		async def scroll_to_text(text: str, browser: BrowserContext):  # type: ignore
			page = await browser.get_current_page()
			try:
				# Try different locator strategies
				locators = [
					page.get_by_text(text, exact=False),
					page.locator(f'text={text}'),
					page.locator(f"//*[contains(text(), '{text}')]"),
				]

				for locator in locators:
					try:
						# First check if element exists and is visible
						if await locator.count() > 0 and await locator.first.is_visible():
							await locator.first.scroll_into_view_if_needed()
							await asyncio.sleep(0.5)  # Wait for scroll to complete
							msg = f'🔍  Scrolled to text: {text}'
							logger.info(msg)
							return ActionResult(extracted_content=msg, include_in_memory=True)
					except Exception as e:
						logger.debug(f'Locator attempt failed: {str(e)}')
						continue

				msg = f"Text '{text}' not found or not visible on page"
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				msg = f"Failed to scroll to text '{text}': {str(e)}"
				logger.error(msg)
				return ActionResult(error=msg, include_in_memory=True)

		@self.registry.action(
			description='Automatically scroll down to find specific text or element type. Useful when expected elements like "Buy Now", "Add to Cart" are not visible.',
		)
		async def auto_scroll_find(text: str, browser: BrowserContext, max_scrolls: int = 3):  # type: ignore
			page = await browser.get_current_page()
			
			for scroll_attempt in range(max_scrolls):
				try:
					# Check if the text exists on current view
					if await page.get_by_text(text, exact=False).count() > 0:
						msg = f'🔍  Found "{text}" after {scroll_attempt} scrolls'
						logger.info(msg)
						return ActionResult(extracted_content=msg, include_in_memory=True)
					
					# Scroll down and wait a bit for content to load
					await page.evaluate('window.scrollBy(0, window.innerHeight);')
					await asyncio.sleep(1)
					
				except Exception as e:
					logger.debug(f'Auto scroll attempt {scroll_attempt} failed: {str(e)}')
					continue
			
			msg = f'🔍  Could not find "{text}" after {max_scrolls} scroll attempts'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='Smart scroll to find common shopping/purchase elements like "Buy Now", "Add to Cart", "Checkout", etc. Useful for e-commerce sites.',
		)
		async def find_purchase_elements(browser: BrowserContext):  # type: ignore
			page = await browser.get_current_page()
			
			# Common purchase-related texts to look for
			purchase_texts = [
				"Buy Now", "Add to Cart", "Add to Bag", "Purchase", "Order Now", 
				"Checkout", "Proceed to Checkout", "Continue", "Place Order", 
				"Add to Basket", "Buy", "Shop Now", "Get Now"
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
						return ActionResult(extracted_content=msg, include_in_memory=True)
					
					# Scroll down and wait for content to load
					await page.evaluate('window.scrollBy(0, window.innerHeight);')
					await asyncio.sleep(1.5)
					
				except Exception as e:
					logger.debug(f'Purchase element search attempt {scroll_attempt} failed: {str(e)}')
					continue
			
			msg = f'🛒  Could not find purchase elements after 5 scroll attempts'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='Get all options from a native dropdown',
		)
		async def get_dropdown_options(index: int, browser: BrowserContext) -> ActionResult:
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
							logger.debug(f'Found dropdown in frame {frame_index}')
							logger.debug(f'Dropdown ID: {options["id"]}, Name: {options["name"]}')

							formatted_options = []
							for opt in options['options']:
								# encoding ensures AI uses the exact string in select_dropdown_option
								encoded_text = json.dumps(opt['text'])
								formatted_options.append(f'{opt["index"]}: text={encoded_text}')

							all_options.extend(formatted_options)

					except Exception as frame_e:
						logger.debug(f'Frame {frame_index} evaluation failed: {str(frame_e)}')

					frame_index += 1

				if all_options:
					msg = '\n'.join(all_options)
					msg += '\nUse the exact text string in select_dropdown_option'
					logger.info(msg)
					return ActionResult(extracted_content=msg, include_in_memory=True)
				else:
					msg = 'No options found in any frame for dropdown'
					logger.info(msg)
					return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				logger.error(f'Failed to get dropdown options: {str(e)}')
				msg = f'Error getting options: {str(e)}'
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='Select dropdown option for interactive element index by the text of the option you want to select',
		)
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
			if dom_element.tag_name != 'select':
				logger.error(f'Element is not a select! Tag: {dom_element.tag_name}, Attributes: {dom_element.attributes}')
				msg = f'Cannot select option: Element with index {index} is a {dom_element.tag_name}, not a select'
				return ActionResult(extracted_content=msg, include_in_memory=True)

			logger.debug(f"Attempting to select '{text}' using xpath: {dom_element.xpath}")
			logger.debug(f'Element attributes: {dom_element.attributes}')
			logger.debug(f'Element tag: {dom_element.tag_name}')

			xpath = '//' + dom_element.xpath

			try:
				frame_index = 0
				for frame in page.frames:
					try:
						logger.debug(f'Trying frame {frame_index} URL: {frame.url}')

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

						dropdown_info = await frame.evaluate(find_dropdown_js, dom_element.xpath)

						if dropdown_info:
							if not dropdown_info.get('found'):
								logger.error(f'Frame {frame_index} error: {dropdown_info.get("error")}')
								continue

							logger.debug(f'Found dropdown in frame {frame_index}: {dropdown_info}')

							# "label" because we are selecting by text
							# nth(0) to disable error thrown by strict mode
							# timeout=1000 because we are already waiting for all network events, therefore ideally we don't need to wait a lot here (default 30s)
							selected_option_values = (
								await frame.locator('//' + dom_element.xpath).nth(0).select_option(label=text, timeout=1000)
							)

							msg = f'selected option {text} with value {selected_option_values}'
							logger.info(msg + f' in frame {frame_index}')

							return ActionResult(extracted_content=msg, include_in_memory=True)

					except Exception as frame_e:
						logger.error(f'Frame {frame_index} attempt failed: {str(frame_e)}')
						logger.error(f'Frame type: {type(frame)}')
						logger.error(f'Frame URL: {frame.url}')

					frame_index += 1

				msg = f"Could not select option '{text}' in any frame"
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				msg = f'Selection failed: {str(e)}'
				logger.error(msg)
				return ActionResult(error=msg, include_in_memory=True)

		# User Assistance Actions
		@self.registry.action(
			'Request help from user for situations requiring human intervention: CAPTCHAs/verifications, login/signup forms, payment processing, sensitive data entry, or any complex authentication. Use this instead of attempting these tasks automatically to respect user privacy and security.',
			param_model=RequestUserHelpAction,
		)
		async def request_user_help(params: RequestUserHelpAction, browser: BrowserContext):
			msg = f'🙋‍♂️ Requesting user help: {params.message}'
			logger.warning(msg)
			logger.warning(f'Reason: {params.reason}')
			
			# Get current page info to help user understand context
			try:
				page = await browser.get_current_page()
				current_url = page.url
				logger.info(f'Current page: {current_url}')
			except Exception as e:
				current_url = "Unknown"
			
			# This will create a special result that signals the web interface to pause and request user input
			return ActionResult(
				extracted_content=f"{msg} - Please check the browser window at {current_url}", 
				include_in_memory=True,
				requires_user_action=True,
				user_input_request={
					'type': 'intervention',
					'reason': params.reason,
					'message': params.message,
					'url': current_url
				}
			)

		@self.registry.action(
			'Ask the user a clarifying question when you need more information to complete the task properly. Use this when: you are unsure about user preferences, need to choose between multiple options, or require specific details not provided in the original task. This enables interactive, conversational automation.',
			param_model=AskUserQuestionAction,
		)
		async def ask_user_question(params: AskUserQuestionAction, browser: BrowserContext):
			msg = f'❓ Agent question: {params.question}'
			logger.info(msg)
			logger.info(f'Context: {params.context}')
			if params.options:
				logger.info(f'Suggested options: {", ".join(params.options)}')
			
			# This will create a special result that signals the web interface to pause and wait for user answer
			return ActionResult(
				extracted_content=f"{msg} (Context: {params.context})",
				include_in_memory=True,
				requires_user_action=True,
				user_input_request={
					'type': 'question',
					'question': params.question,
					'context': params.context,
					'options': params.options
				}
			)

	def action(self, description: str, **kwargs):
		"""Decorator for registering custom actions

		@param description: Describe the LLM what the function does (better description == better function calling)
		"""
		return self.registry.action(description, **kwargs)

	@observe(name='controller.multi_act')
	@time_execution_async('--multi-act')
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
		cached_path_hashes = set(e.hash.branch_path_hash for e in cached_selector_map.values())

		check_break_if_paused()

		await browser_context.remove_highlights()

		for i, action in enumerate(actions):
			check_break_if_paused()

			if action.get_index() is not None and i != 0:
				new_state = await browser_context.get_state()
				new_path_hashes = set(e.hash.branch_path_hash for e in new_state.selector_map.values())
				if check_for_new_elements and not new_path_hashes.issubset(cached_path_hashes):
					# next action requires index but there are new elements on the page
					msg = f'Something new appeared after action {i} / {len(actions)}'
					logger.info(msg)
					results.append(ActionResult(extracted_content=msg, include_in_memory=True))
					break

			check_break_if_paused()

			results.append(await self.act(action, browser_context, page_extraction_llm, sensitive_data, available_file_paths))

			logger.debug(f'Executed action {i + 1} / {len(actions)}')
			if results[-1].is_done or results[-1].error or i == len(actions) - 1:
				break

			await asyncio.sleep(browser_context.config.wait_between_actions)
			# hash all elements. if it is a subset of cached_state its fine - else break (new elements on page)

		return results

	@time_execution_sync('--act')
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
							'action': action_name,
							'params': params,
						},
						span_type='TOOL',
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
						raise ValueError(f'Invalid action result type: {type(result)} of {result}')
			return ActionResult()
		except Exception as e:
			raise e
