"""Web scraper for tgju.org (Iranian gold & currency prices).

TGJU shows prices in Rial; we convert to Toman (divide by 10).
NOTE: scrapers depend on the page's HTML. If TGJU changes its layout, update
PRICE_ATTRIBUTES below - that is the only place that needs to change.
"""
import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.tgju.org/profile/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.8",
}
# HTML attributes that mark the price element. Tried in order; the first match wins.
PRICE_ATTRIBUTES = [
    {"data-col": "info.last_trade.PDrCotVal"},
]

_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


class TgjuScraperError(Exception):
    """Raised when the page can't be downloaded or the price can't be found."""


def parse_price_text(text):
    """'۲٬۶۸۸٬۲۰۰' or '2,688,200' -> 2688200.0"""
    cleaned = text.translate(_DIGIT_MAP)
    cleaned = re.sub(r"[,٬،\s]", "", cleaned)
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    if not match:
        raise TgjuScraperError(f"No number found in {text!r}")
    return float(match.group())


def parse_price_from_html(html):
    """Return the price (in Rial) found in a TGJU profile page."""
    soup = BeautifulSoup(html, "html.parser")
    for attrs in PRICE_ATTRIBUTES:
        element = soup.find(attrs=attrs)
        if element and element.get_text(strip=True):
            return parse_price_text(element.get_text(strip=True))
    raise TgjuScraperError("Price element not found - the page layout may have changed")


def get_price_toman(slug, timeout=10):
    """Download https://www.tgju.org/profile/<slug> and return the price in Toman."""
    try:
        response = requests.get(BASE_URL + slug, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise TgjuScraperError(f"TGJU request failed for {slug}: {exc}") from exc
    return parse_price_from_html(response.text) / 10
