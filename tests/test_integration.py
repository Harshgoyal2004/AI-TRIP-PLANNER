"""Live tests against the real APIs. Opt-in:

    pytest -m integration      # each tool against its real API (cheap, ~15s)
    pytest -m e2e              # one full agent run through Groq/OpenAI (~1 min, uses LLM tokens)

Each test is skipped when the API key it needs is missing from the environment / .env.
"""
import os
import re

import pytest
from dotenv import load_dotenv

load_dotenv()


def needs(*keys):
    missing = [k for k in keys if not os.getenv(k)]
    return pytest.mark.skipif(bool(missing), reason=f"missing {', '.join(missing)}")


# ---------------------------------------------------------------- tools vs real APIs

@pytest.mark.integration
@needs("OPENWEATHERMAP_API_KEY")
def test_live_current_weather():
    from tools import get_current_weather

    out = get_current_weather.invoke({"place": "Mumbai"})
    assert out.startswith("Weather in Mumbai"), out
    assert re.search(r"-?\d+(\.\d+)?°C", out), out


@pytest.mark.integration
@needs("OPENWEATHERMAP_API_KEY")
def test_live_weather_forecast():
    from tools import get_weather_forecast

    out = get_weather_forecast.invoke({"city": "Mumbai", "days": 2})
    assert out.startswith("2-day forecast for Mumbai"), out
    assert out.count("°C") >= 2, out


@pytest.mark.integration
@needs("OPENWEATHERMAP_API_KEY")
def test_live_weather_unknown_city_returns_message():
    from tools import get_current_weather

    out = get_current_weather.invoke({"place": "Qwxzvbnm-not-a-city"})
    assert out.startswith("Could not fetch weather"), out


@pytest.mark.integration
@needs("EXCHANGE_RATE_API_KEY")
def test_live_exchange_rates_include_inr():
    from tools import get_exchange_rates

    out = get_exchange_rates.invoke({"base_currency": "USD"})
    match = re.search(r"([\d.]+) INR", out)
    assert match, out
    assert 50 < float(match.group(1)) < 200, f"implausible USD→INR rate: {out}"


@pytest.mark.integration
@needs("EXCHANGE_RATE_API_KEY")
def test_live_convert_currency():
    from tools import convert_currency

    out = convert_currency.invoke({"amount": 100, "from_currency": "usd", "to_currency": "inr"})
    assert out.startswith("100.0 USD = ") and "INR" in out, out


@pytest.mark.integration
@needs("GPLACES_API_KEY")
@pytest.mark.parametrize("tool_name", ["search_attractions", "search_restaurants"])
def test_live_google_places(tool_name):
    import tools

    out = getattr(tools, tool_name).invoke({"place": "Jaipur"})
    assert "(Google Places)" in out, out[:300]
    assert "Address:" in out and "Google place ID" not in out, out[:300]


@pytest.mark.integration
@needs("TAVILY_API_KEY")
def test_live_tavily_fallback(monkeypatch):
    import tools

    monkeypatch.setattr(tools, "_google", lambda: None)  # force the fallback path
    out = tools.search_attractions.invoke({"place": "Jaipur"})
    assert "(web search)" in out, out[:300]
    assert "web search also failed" not in out, out[:300]
    assert len(out) <= tools.MAX_WEB_CHARS + 200


# ---------------------------------------------------------------- full agent run

@pytest.mark.e2e
@needs("GROQ_API_KEY", "OPENWEATHERMAP_API_KEY", "EXCHANGE_RATE_API_KEY")
def test_agent_plans_a_trip_end_to_end(tmp_path_factory):
    from langchain_core.messages import AIMessage, HumanMessage

    from agent import build_agent

    out = build_agent().invoke(
        {"messages": [HumanMessage(content="Plan a 2-day trip to Jaipur with a total budget of about ₹20,000.")]},
        {"recursion_limit": 40},
    )
    called = {c["name"] for m in out["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])}
    # LLMs often emit non-breaking / narrow spaces (e.g. "Day\u00a01", "29\u202f°C"); normalise before matching
    answer = re.sub(r"\s", " ", out["messages"][-1].content)
    # Keep the plan for inspection when an assertion below fails
    (tmp_path_factory.mktemp("e2e") / "answer.md").write_text(answer, encoding="utf-8")
    print(f"\nTools called: {sorted(called)}\n--- answer ---\n{answer}")

    # Tools the prompt makes mandatory
    assert {"get_current_weather", "get_exchange_rates"} <= called, called
    assert called & {"search_attractions", "search_restaurants"}, called

    # The itinerary follows the required format
    assert "°C" in answer and "₹" in answer, answer[:500]
    assert "Day 1" in answer and "Day 2" in answer, answer[:500]
    assert re.search(r"\]\(https://www\.google\.com/maps/search/\?api=1&query=", answer), "no Markdown map links"
