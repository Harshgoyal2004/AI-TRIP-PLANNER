"""Tools the agent can call. Each docstring is the description the LLM sees, so keep them short.

Tools return error messages as text instead of raising, so one failing API doesn't abort the whole plan.
API keys are read when a tool runs, so importing this module never needs keys.
"""
import logging
import os
from collections import Counter
from datetime import datetime
from functools import lru_cache

import requests
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------- weather (OpenWeatherMap)

def _weather(endpoint: str, **params) -> dict:
    key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not key:
        raise RuntimeError("OPENWEATHERMAP_API_KEY is not set")
    resp = requests.get(f"https://api.openweathermap.org/data/2.5/{endpoint}",
                        params={**params, "appid": key, "units": "metric"}, timeout=15)
    resp.raise_for_status()
    return resp.json()


@tool
def get_current_weather(place: str) -> str:
    """Get the current weather for a city, e.g. 'Goa' or 'London,uk'."""
    try:
        d = _weather("weather", q=place)
    except Exception as e:
        return f"Could not fetch weather for {place}: {e}"
    main, desc = d.get("main", {}), d.get("weather", [{}])[0].get("description", "n/a")
    return (
        f"Weather in {d.get('name', place)}, {d.get('sys', {}).get('country', '')}: {desc}, "
        f"{main.get('temp')}°C (feels like {main.get('feels_like')}°C), "
        f"humidity {main.get('humidity')}%, wind {d.get('wind', {}).get('speed')} m/s"
    )


@tool
def get_weather_forecast(city: str, days: int = 3) -> str:
    """Get a daily weather forecast (1-5 days) for a city."""
    days = max(1, min(5, int(days)))
    try:
        d = _weather("forecast", q=city, cnt=days * 8)  # 8 readings per day (3-hour steps)
    except Exception as e:
        return f"Could not fetch forecast for {city}: {e}"

    by_day: dict[str, list] = {}
    for item in d.get("list", []):
        by_day.setdefault(datetime.fromtimestamp(item["dt"]).strftime("%a %d %b"), []).append(item)

    lines = [f"{days}-day forecast for {d.get('city', {}).get('name', city)}:"]
    for day, items in list(by_day.items())[:days]:
        temps = [i["main"]["temp"] for i in items]
        condition = Counter(i["weather"][0]["description"] for i in items).most_common(1)[0][0]
        lines.append(f"- {day}: {min(temps):.0f}–{max(temps):.0f}°C, {condition}")
    return "\n".join(lines)


# ---------------------------------------------------------------- currency (ExchangeRate API)

COMMON_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"]


def _rates(base: str) -> dict[str, float]:
    key = os.getenv("EXCHANGE_RATE_API_KEY")
    if not key:
        raise RuntimeError("EXCHANGE_RATE_API_KEY is not set")
    resp = requests.get(f"https://v6.exchangerate-api.com/v6/{key}/latest/{base.upper()}", timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("result") != "success":
        raise RuntimeError(data.get("error-type", "unknown API error"))
    return data["conversion_rates"]


@tool
def get_exchange_rates(base_currency: str = "USD") -> str:
    """Get exchange rates from a base currency (e.g. 'USD') to major currencies, including INR."""
    base = base_currency.upper()
    try:
        rates = _rates(base)
    except Exception as e:
        return f"Could not fetch exchange rates: {e}"
    return f"1 {base} = " + ", ".join(f"{rates[c]:.4f} {c}" for c in COMMON_CURRENCIES if c != base and c in rates)


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between two currencies, e.g. 100 USD to INR."""
    src, dst = from_currency.upper(), to_currency.upper()
    try:
        rate = _rates(src)[dst]
    except KeyError:
        return f"Unknown currency: {dst}"
    except Exception as e:
        return f"Could not convert currency: {e}"
    return f"{amount} {src} = {amount * rate:.2f} {dst} (1 {src} = {rate:.4f} {dst})"


# ---------------------------------------------------------------- places (Google Places, Tavily fallback)

# Tool output is resent to the LLM on every agent step, and Groq's on-demand tier
# caps requests at ~8k tokens/minute, so keep results short.
MAX_PLACES = 6
MAX_WEB_CHARS = 1500
_DROP_PREFIXES = ("Google place ID:", "Phone:", "Website: Unknown")
_GOOGLE_EMPTY = "Google Places did not find any places"

PLACE_QUERIES = {
    "attractions": "top tourist attractions in and around {place}",
    "restaurants": "top restaurants and eateries in and around {place}",
    "activities": "things to do and activities in and around {place}",
    "transportation": "transportation options in and around {place}",
}


@lru_cache(maxsize=1)
def _google():
    """GooglePlacesTool, or None when no key is configured (all searches then use Tavily)."""
    key = os.getenv("GPLACES_API_KEY")
    if not key:
        return None
    try:
        from langchain_google_community import GooglePlacesAPIWrapper, GooglePlacesTool

        return GooglePlacesTool(api_wrapper=GooglePlacesAPIWrapper(gplaces_api_key=key, top_k_results=MAX_PLACES))
    except Exception as e:
        logger.warning(f"Google Places unavailable, using Tavily only: {e}")
        return None


def _web_search(query: str) -> str:
    from langchain_tavily import TavilySearch

    result = TavilySearch(topic="general", include_answer="advanced", max_results=3).invoke({"query": query})
    if isinstance(result, dict) and result.get("answer"):
        return result["answer"][:MAX_WEB_CHARS]
    return str(result)[:MAX_WEB_CHARS]


def _compact(text: str) -> str:
    """Drop low-value lines (place IDs, phone numbers, unknown websites) from Google output."""
    return "\n".join(ln for ln in str(text).splitlines() if ln.strip() and not ln.strip().startswith(_DROP_PREFIXES))


def _search_places(topic: str, place: str) -> str:
    query = PLACE_QUERIES[topic].format(place=place)
    reason = "Google Places is not configured"
    google = _google()
    if google is not None:
        try:
            result = google.run(query)
            if result and not result.startswith(_GOOGLE_EMPTY):
                return f"{topic.capitalize()} in {place} (Google Places):\n{_compact(result)}"
            reason = "Google Places found no results"
        except Exception as e:
            reason = f"Google Places failed ({e})"
    try:
        return f"{reason}. {topic.capitalize()} in {place} (web search):\n{_web_search(query)}"
    except Exception as e:
        return f"Could not find {topic} in {place}: {reason}; web search also failed ({e})."


@tool
def search_attractions(place: str) -> str:
    """Find top tourist attractions in a place."""
    return _search_places("attractions", place)


@tool
def search_restaurants(place: str) -> str:
    """Find popular restaurants in a place."""
    return _search_places("restaurants", place)


@tool
def search_activities(place: str) -> str:
    """Find activities and things to do in a place."""
    return _search_places("activities", place)


@tool
def search_transportation(place: str) -> str:
    """Find transportation options in or to a place."""
    return _search_places("transportation", place)


# ---------------------------------------------------------------- calculator

@tool
def estimate_total_hotel_cost(price_per_night: float, total_days: float) -> float:
    """Total hotel cost: price per night × number of nights."""
    return price_per_night * total_days


@tool
def calculate_total_expense(costs: list[float]) -> float:
    """Add up a list of costs."""
    return sum(costs)


@tool
def calculate_daily_expense_budget(total_cost: float, days: float) -> float:
    """Daily budget: total cost ÷ number of days."""
    return total_cost / days if days > 0 else 0.0


ALL_TOOLS = [
    get_current_weather,
    get_weather_forecast,
    get_exchange_rates,
    convert_currency,
    search_attractions,
    search_restaurants,
    search_activities,
    search_transportation,
    estimate_total_hotel_cost,
    calculate_total_expense,
    calculate_daily_expense_budget,
]
