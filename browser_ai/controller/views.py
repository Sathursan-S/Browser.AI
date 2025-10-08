from typing import Optional

from pydantic import BaseModel, model_validator


# Action Input Models
class SearchGoogleAction(BaseModel):
	query: str


class SearchYouTubeAction(BaseModel):
	query: str


class SearchEcommerceAction(BaseModel):
	query: str
	site: Optional[str] = None  # e.g., 'daraz.lk', 'ikman.lk', 'glomark.lk', 'amazon.com', 'ebay.com', etc.


class FindBestWebsiteAction(BaseModel):
	purpose: str  # What you want to do (e.g., "buy gaming laptop", "download python tutorial", "find vintage records")
	category: str  # Category: "shopping", "download", "information", "service", or "other"


class DetectLocationAction(BaseModel):
	"""Action to detect user's geographic location for localized shopping"""
	pass  # No parameters needed


class GoToUrlAction(BaseModel):
	url: str


class ClickElementAction(BaseModel):
	index: int
	xpath: Optional[str] = None


class InputTextAction(BaseModel):
	index: int
	text: str
	xpath: Optional[str] = None


class DoneAction(BaseModel):
	text: str


class SwitchTabAction(BaseModel):
	page_id: int


class OpenTabAction(BaseModel):
	url: str


class ScrollAction(BaseModel):
	amount: Optional[int] = None  # The number of pixels to scroll. If None, scroll down/up one page


class SendKeysAction(BaseModel):
	keys: str


class ExtractPageContentAction(BaseModel):
    value: str

class RequestUserHelpAction(BaseModel):
	message: str  # Clear message explaining what the user needs to do
	reason: str  # Type of intervention: "captcha", "authentication", "payment", "verification", "personal_data", "complex_form"


class AskUserQuestionAction(BaseModel):
	"""
	Action for agent to ask clarifying questions during task execution.
	Different from request_user_help which is for technical interventions (CAPTCHA, login, etc.)
	This is for when the agent needs more information to complete the task properly.
	"""
	question: str  # The specific question to ask the user
	context: str  # Why this information is needed (helps user understand)
	options: list[str] = []  # Optional: Suggested answers/options for the user to choose from

	
class NoParamsAction(BaseModel):
	"""
	Accepts absolutely anything in the incoming data
	and discards it, so the final parsed model is empty.
	"""

	@model_validator(mode='before')
	def ignore_all_inputs(cls, values):
		# No matter what the user sends, discard it and return empty.
		return {}

	class Config:
		# If you want to silently allow unknown fields at top-level,
		# set extra = 'allow' as well:
		extra = 'allow'
