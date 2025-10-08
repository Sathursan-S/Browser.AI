"""
User Location Detection Service

Detects user's geographic location to provide context-aware shopping experiences,
including currency detection, regional website suggestions, and localized content.
"""

import logging
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Region(Enum):
    """Geographic regions for location-based services"""
    NORTH_AMERICA = "North America"
    SOUTH_AMERICA = "South America"
    EUROPE = "Europe"
    ASIA = "Asia"
    MIDDLE_EAST = "Middle East"
    AFRICA = "Africa"
    OCEANIA = "Oceania"


@dataclass
class LocationInfo:
    """User location information"""
    country: str
    country_code: str  # ISO 3166-1 alpha-2 (e.g., "US", "LK", "GB")
    region: Region
    currency: str  # ISO 4217 currency code (e.g., "USD", "LKR", "EUR")
    currency_symbol: str  # Symbol (e.g., "$", "Rs", "€")
    language: str  # Primary language code (e.g., "en", "si", "ta")
    timezone: str  # IANA timezone (e.g., "America/New_York", "Asia/Colombo")
    preferred_ecommerce_sites: list[str]  # Ordered list of popular sites
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region.value,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "language": self.language,
            "timezone": self.timezone,
            "preferred_ecommerce_sites": self.preferred_ecommerce_sites
        }


# Comprehensive location database
LOCATION_DATABASE = {
    # North America
    "US": LocationInfo(
        country="United States",
        country_code="US",
        region=Region.NORTH_AMERICA,
        currency="USD",
        currency_symbol="$",
        language="en",
        timezone="America/New_York",
        preferred_ecommerce_sites=["amazon.com", "walmart.com", "ebay.com", "target.com", "bestbuy.com"]
    ),
    "CA": LocationInfo(
        country="Canada",
        country_code="CA",
        region=Region.NORTH_AMERICA,
        currency="CAD",
        currency_symbol="C$",
        language="en",
        timezone="America/Toronto",
        preferred_ecommerce_sites=["amazon.ca", "walmart.ca", "ebay.ca", "canadiantire.ca"]
    ),
    
    # Europe
    "GB": LocationInfo(
        country="United Kingdom",
        country_code="GB",
        region=Region.EUROPE,
        currency="GBP",
        currency_symbol="£",
        language="en",
        timezone="Europe/London",
        preferred_ecommerce_sites=["amazon.co.uk", "ebay.co.uk", "argos.co.uk", "johnlewis.com"]
    ),
    "DE": LocationInfo(
        country="Germany",
        country_code="DE",
        region=Region.EUROPE,
        currency="EUR",
        currency_symbol="€",
        language="de",
        timezone="Europe/Berlin",
        preferred_ecommerce_sites=["amazon.de", "ebay.de", "otto.de", "mediamarkt.de"]
    ),
    "FR": LocationInfo(
        country="France",
        country_code="FR",
        region=Region.EUROPE,
        currency="EUR",
        currency_symbol="€",
        language="fr",
        timezone="Europe/Paris",
        preferred_ecommerce_sites=["amazon.fr", "cdiscount.com", "fnac.com", "ebay.fr"]
    ),
    
    # Asia - South Asia
    "LK": LocationInfo(
        country="Sri Lanka",
        country_code="LK",
        region=Region.ASIA,
        currency="LKR",
        currency_symbol="Rs",
        language="si",
        timezone="Asia/Colombo",
        preferred_ecommerce_sites=["daraz.lk", "ikman.lk", "glomark.lk", "kapruka.com", "mydeal.lk"]
    ),
    "IN": LocationInfo(
        country="India",
        country_code="IN",
        region=Region.ASIA,
        currency="INR",
        currency_symbol="₹",
        language="hi",
        timezone="Asia/Kolkata",
        preferred_ecommerce_sites=["amazon.in", "flipkart.com", "snapdeal.com", "myntra.com"]
    ),
    "PK": LocationInfo(
        country="Pakistan",
        country_code="PK",
        region=Region.ASIA,
        currency="PKR",
        currency_symbol="₨",
        language="ur",
        timezone="Asia/Karachi",
        preferred_ecommerce_sites=["daraz.pk", "alibaba.pk", "goto.com.pk"]
    ),
    
    # Asia - East Asia
    "CN": LocationInfo(
        country="China",
        country_code="CN",
        region=Region.ASIA,
        currency="CNY",
        currency_symbol="¥",
        language="zh",
        timezone="Asia/Shanghai",
        preferred_ecommerce_sites=["taobao.com", "jd.com", "alibaba.com", "tmall.com"]
    ),
    "JP": LocationInfo(
        country="Japan",
        country_code="JP",
        region=Region.ASIA,
        currency="JPY",
        currency_symbol="¥",
        language="ja",
        timezone="Asia/Tokyo",
        preferred_ecommerce_sites=["amazon.co.jp", "rakuten.co.jp", "yahoo.co.jp"]
    ),
    "KR": LocationInfo(
        country="South Korea",
        country_code="KR",
        region=Region.ASIA,
        currency="KRW",
        currency_symbol="₩",
        language="ko",
        timezone="Asia/Seoul",
        preferred_ecommerce_sites=["coupang.com", "gmarket.co.kr", "11st.co.kr"]
    ),
    
    # Asia - Southeast Asia
    "SG": LocationInfo(
        country="Singapore",
        country_code="SG",
        region=Region.ASIA,
        currency="SGD",
        currency_symbol="S$",
        language="en",
        timezone="Asia/Singapore",
        preferred_ecommerce_sites=["lazada.sg", "shopee.sg", "qoo10.sg", "amazon.sg"]
    ),
    "MY": LocationInfo(
        country="Malaysia",
        country_code="MY",
        region=Region.ASIA,
        currency="MYR",
        currency_symbol="RM",
        language="ms",
        timezone="Asia/Kuala_Lumpur",
        preferred_ecommerce_sites=["lazada.com.my", "shopee.com.my", "mudah.my"]
    ),
    "TH": LocationInfo(
        country="Thailand",
        country_code="TH",
        region=Region.ASIA,
        currency="THB",
        currency_symbol="฿",
        language="th",
        timezone="Asia/Bangkok",
        preferred_ecommerce_sites=["lazada.co.th", "shopee.co.th", "jd.co.th"]
    ),
    "PH": LocationInfo(
        country="Philippines",
        country_code="PH",
        region=Region.ASIA,
        currency="PHP",
        currency_symbol="₱",
        language="en",
        timezone="Asia/Manila",
        preferred_ecommerce_sites=["lazada.com.ph", "shopee.ph", "zalora.com.ph"]
    ),
    
    # Middle East
    "AE": LocationInfo(
        country="United Arab Emirates",
        country_code="AE",
        region=Region.MIDDLE_EAST,
        currency="AED",
        currency_symbol="د.إ",
        language="ar",
        timezone="Asia/Dubai",
        preferred_ecommerce_sites=["amazon.ae", "noon.com", "souq.com", "carrefour.ae"]
    ),
    "SA": LocationInfo(
        country="Saudi Arabia",
        country_code="SA",
        region=Region.MIDDLE_EAST,
        currency="SAR",
        currency_symbol="ر.س",
        language="ar",
        timezone="Asia/Riyadh",
        preferred_ecommerce_sites=["amazon.sa", "noon.com", "jarir.com", "extra.com"]
    ),
    
    # Oceania
    "AU": LocationInfo(
        country="Australia",
        country_code="AU",
        region=Region.OCEANIA,
        currency="AUD",
        currency_symbol="A$",
        language="en",
        timezone="Australia/Sydney",
        preferred_ecommerce_sites=["amazon.com.au", "ebay.com.au", "kogan.com", "catch.com.au"]
    ),
    "NZ": LocationInfo(
        country="New Zealand",
        country_code="NZ",
        region=Region.OCEANIA,
        currency="NZD",
        currency_symbol="NZ$",
        language="en",
        timezone="Pacific/Auckland",
        preferred_ecommerce_sites=["trademe.co.nz", "themarket.co.nz", "mighty ape.co.nz"]
    ),
}


class LocationDetector:
    """Detects and manages user location information"""
    
    def __init__(self):
        self.detected_location: Optional[LocationInfo] = None
        self._detection_attempted = False
    
    async def detect_location_from_browser(self, browser_context) -> Optional[LocationInfo]:
        """
        Detect location using browser's geolocation API
        
        Args:
            browser_context: BrowserContext instance
            
        Returns:
            LocationInfo if detected, None otherwise
        """
        try:
            page = await browser_context.get_current_page()
            
            # Use a geolocation detection service
            await page.goto("https://ipapi.co/json/", wait_until="networkidle")
            await page.wait_for_load_state("networkidle")
            
            # Extract JSON content
            content = await page.content()
            
            # Parse the JSON response (simple regex extraction)
            country_code_match = re.search(r'"country_code":\s*"([A-Z]{2})"', content)
            
            if country_code_match:
                country_code = country_code_match.group(1)
                location_info = LOCATION_DATABASE.get(country_code)
                
                if location_info:
                    self.detected_location = location_info
                    self._detection_attempted = True
                    logger.info(f"✅ Location detected: {location_info.country} ({country_code})")
                    return location_info
                else:
                    logger.warning(f"⚠️ Country code {country_code} not in database, using US as default")
                    self.detected_location = LOCATION_DATABASE["US"]
                    self._detection_attempted = True
                    return self.detected_location
            else:
                logger.warning("⚠️ Could not parse location data, using US as default")
                self.detected_location = LOCATION_DATABASE["US"]
                self._detection_attempted = True
                return self.detected_location
                
        except Exception as e:
            logger.error(f"❌ Location detection failed: {e}")
            # Default to US if detection fails
            self.detected_location = LOCATION_DATABASE["US"]
            self._detection_attempted = True
            return self.detected_location
    
    def get_location(self) -> Optional[LocationInfo]:
        """Get the currently detected location"""
        return self.detected_location
    
    def set_location_manual(self, country_code: str) -> bool:
        """
        Manually set the user's location
        
        Args:
            country_code: ISO 3166-1 alpha-2 country code
            
        Returns:
            True if successful, False if country code not found
        """
        location_info = LOCATION_DATABASE.get(country_code.upper())
        if location_info:
            self.detected_location = location_info
            self._detection_attempted = True
            logger.info(f"📍 Location manually set to: {location_info.country}")
            return True
        else:
            logger.warning(f"⚠️ Country code {country_code} not found in database")
            return False
    
    def get_currency_context(self) -> str:
        """Get a string describing the user's currency context for LLM prompts"""
        if not self.detected_location:
            return "Currency: USD ($). Use US Dollar for all price references."
        
        loc = self.detected_location
        return f"Currency: {loc.currency} ({loc.currency_symbol}). User is in {loc.country}. All prices should be in {loc.currency}."
    
    def get_ecommerce_context(self) -> str:
        """Get a string describing recommended e-commerce sites for LLM prompts"""
        if not self.detected_location:
            return "Recommended shopping sites: amazon.com, ebay.com, walmart.com"
        
        loc = self.detected_location
        sites_list = ", ".join(loc.preferred_ecommerce_sites[:5])  # Top 5
        return f"Recommended shopping sites for {loc.country}: {sites_list}"
    
    def get_full_context(self) -> str:
        """Get complete location context for LLM prompts"""
        if not self.detected_location:
            return "Location: United States (US). Currency: USD ($). Recommended sites: amazon.com, ebay.com"
        
        loc = self.detected_location
        return (
            f"🌍 User Location: {loc.country} ({loc.country_code})\n"
            f"💰 Currency: {loc.currency} ({loc.currency_symbol})\n"
            f"🛒 Preferred E-commerce Sites: {', '.join(loc.preferred_ecommerce_sites[:3])}\n"
            f"🌐 Language: {loc.language}\n"
            f"⏰ Timezone: {loc.timezone}"
        )
    
    def has_detected(self) -> bool:
        """Check if location detection has been attempted"""
        return self._detection_attempted
