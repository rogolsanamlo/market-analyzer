"""Client for the free CoinGecko API (no API key needed, but rate limited)."""
from datetime import datetime, timezone

import requests

BASE_URL = "https://api.coingecko.com/api/v3"


class CoinGeckoError(Exception):
    """Raised when CoinGecko can't be reached or returns something unexpected."""


def _get(path, params, timeout):
    try:
        response = requests.get(
            BASE_URL + path, params=params, timeout=timeout,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise CoinGeckoError(f"CoinGecko request failed: {exc}") from exc


def parse_simple_price(data, coin_ids, vs_currency="usd"):
    """{'bitcoin': {'usd': 65000}} -> {'bitcoin': 65000.0}"""
    result = {}
    for coin_id in coin_ids:
        try:
            result[coin_id] = float(data[coin_id][vs_currency])
        except (KeyError, TypeError, ValueError):
            continue
    return result


def parse_market_chart(data):
    """{'prices': [[ms, price], ...]} -> [(datetime in UTC, price), ...]"""
    try:
        raw = data["prices"]
        return [
            (datetime.fromtimestamp(ms / 1000, timezone.utc).replace(microsecond=0), float(price))
            for ms, price in raw
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise CoinGeckoError(f"Unexpected market_chart response: {exc}") from exc


def get_current_prices(coin_ids, vs_currency="usd", timeout=10):
    data = _get(
        "/simple/price",
        {"ids": ",".join(coin_ids), "vs_currencies": vs_currency},
        timeout,
    )
    return parse_simple_price(data, coin_ids, vs_currency)


def get_history(coin_id, days=30, vs_currency="usd", timeout=10):
    data = _get(
        f"/coins/{coin_id}/market_chart",
        {"vs_currency": vs_currency, "days": days, "interval": "daily"},
        timeout,
    )
    return parse_market_chart(data)
