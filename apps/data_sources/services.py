"""Decides where each asset's data comes from and saves it.

  has an API  -> API client (CoinGecko)
  no API      -> web scraper (TGJU)

One failing source never stops the others; every result is reported back.
"""
import logging

from apps.market_data import queries
from apps.market_data.models import MIN_REAL_POINTS, Asset

from .api_clients import coingecko_client
from .api_clients.coingecko_client import CoinGeckoError
from .scrapers import tgju_scraper
from .scrapers.tgju_scraper import TgjuScraperError

logger = logging.getLogger("apps.data_sources")


def _fetch_crypto(timeout, backfill_days):
    assets = list(Asset.objects.filter(source=Asset.SOURCE_COINGECKO))
    if not assets:
        return []
    try:
        prices = coingecko_client.get_current_prices([a.source_id for a in assets], timeout=timeout)
    except Exception as exc:  # a broken source must never crash the whole refresh
        logger.error("CoinGecko current prices failed: %s", exc, exc_info=not isinstance(exc, CoinGeckoError))
        return [{"symbol": a.symbol, "ok": False, "error": str(exc)} for a in assets]

    results = []
    for asset in assets:
        price = prices.get(asset.source_id)
        if price is None:
            results.append({"symbol": asset.symbol, "ok": False, "error": "no price returned"})
            continue
        queries.add_price(asset, price, "coingecko")
        # First run: download past days too so the chart isn't empty.
        if queries.count_prices(asset, include_demo=False) < MIN_REAL_POINTS:
            try:
                history = coingecko_client.get_history(asset.source_id, days=backfill_days, timeout=timeout)
                queries.add_prices(asset, history, "coingecko")
            except CoinGeckoError as exc:
                logger.warning("History backfill failed for %s: %s", asset.symbol, exc)
        results.append({"symbol": asset.symbol, "ok": True, "price": price})
    return results


def _fetch_tgju(timeout):
    results = []
    for asset in Asset.objects.filter(source=Asset.SOURCE_TGJU):
        try:
            price = tgju_scraper.get_price_toman(asset.source_id, timeout=timeout)
        except Exception as exc:  # a broken page must never crash the whole refresh
            logger.error("TGJU scrape failed for %s: %s", asset.symbol, exc,
                         exc_info=not isinstance(exc, TgjuScraperError))
            results.append({"symbol": asset.symbol, "ok": False, "error": str(exc)})
            continue
        queries.add_price(asset, price, "tgju")
        results.append({"symbol": asset.symbol, "ok": True, "price": price})
    return results


def fetch_all(timeout=10, backfill_days=30):
    """Fetch every asset once. Returns a list of {symbol, ok, price | error}."""
    results = _fetch_crypto(timeout, backfill_days) + _fetch_tgju(timeout)
    ok = sum(1 for r in results if r["ok"])
    logger.info("Fetch finished: %s/%s assets updated", ok, len(results))
    return results
