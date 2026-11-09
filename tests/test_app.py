"""Offline tests (no API keys, no network): tools with mocked APIs, the FastAPI endpoints, and the agent graph."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

import agent
import main
import tools


# ================================================================ tools

def test_all_tools_have_unique_names():
    names = [t.name for t in tools.ALL_TOOLS]
    assert len(names) == 11 and len(set(names)) == 11


def test_hotel_cost_accepts_numeric_strings():
    assert tools.estimate_total_hotel_cost.invoke({"price_per_night": "2500", "total_days": "4"}) == 10000


def test_total_expense():
    assert tools.calculate_total_expense.invoke({"costs": [100.0, 250.5, 49.5]}) == 400


def test_daily_budget_handles_float_strings_and_zero_days():
    assert tools.calculate_daily_expense_budget.invoke({"total_cost": "30000", "days": "5.0"}) == 6000
    assert tools.calculate_daily_expense_budget.invoke({"total_cost": "30000", "days": "0"}) == 0


@pytest.fixture
def web(monkeypatch):
    fake = MagicMock(return_value="Fort Aguada, Baga Beach")
    monkeypatch.setattr(tools, "_web_search", fake)
    return fake


def _use_google(monkeypatch, google):
    monkeypatch.setattr(tools, "_google", lambda: google)


def test_no_google_key_uses_web_search(monkeypatch, web):
    _use_google(monkeypatch, None)
    out = tools.search_attractions.invoke({"place": "Goa"})
    assert "Fort Aguada" in out and "not configured" in out


def test_google_empty_message_falls_back(monkeypatch, web):
    google = MagicMock()
    google.run.return_value = "Google Places did not find any places that match the description"
    _use_google(monkeypatch, google)
    out = tools.search_restaurants.invoke({"place": "Goa"})
    assert "Fort Aguada" in out and "no results" in out


def test_google_error_falls_back(monkeypatch, web):
    google = MagicMock()
    google.run.side_effect = RuntimeError("quota")
    _use_google(monkeypatch, google)
    out = tools.search_activities.invoke({"place": "Goa"})
    assert "Fort Aguada" in out and "quota" in out


def test_google_success_is_compacted_and_skips_web(monkeypatch, web):
    google = MagicMock()
    google.run.return_value = (
        "1. Kadamba Bus Stand\nAddress: Panaji\nGoogle place ID: abc123\nPhone: 0832 000\nWebsite: Unknown\n"
    )
    _use_google(monkeypatch, google)
    out = tools.search_transportation.invoke({"place": "Goa"})
    assert "Kadamba" in out and "Panaji" in out
    assert "place ID" not in out and "Phone" not in out and "Website" not in out
    web.assert_not_called()


def test_current_weather_formats_celsius(monkeypatch):
    monkeypatch.setattr(tools, "_weather", lambda endpoint, **p: {
        "name": "Panaji", "sys": {"country": "IN"},
        "main": {"temp": 29.5, "feels_like": 33, "humidity": 70},
        "weather": [{"description": "scattered clouds"}], "wind": {"speed": 3},
    })
    out = tools.get_current_weather.invoke({"place": "Goa"})
    assert out.startswith("Weather in Panaji, IN") and "29.5°C" in out


def test_weather_without_key_returns_message(monkeypatch):
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    out = tools.get_current_weather.invoke({"place": "Goa"})
    assert "OPENWEATHERMAP_API_KEY is not set" in out


# ================================================================ API (fake agent)

class FakeAgent:
    def __init__(self, answer="# 🌍 Dream Trip to Goa", error=None):
        self.answer, self.error, self.calls = answer, error, []

    def invoke(self, state):
        self.calls.append(state)
        if self.error:
            raise self.error
        return {"messages": [*state["messages"], AIMessage(content=self.answer)]}


@pytest.fixture
def client():
    return TestClient(main.app)


def use_agent(monkeypatch, fake):
    monkeypatch.setattr(main, "get_agent", lambda: fake)
    return fake


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200 and resp.json() == {"status": "ok"}


def test_query_returns_last_message_and_passes_question(client, monkeypatch):
    fake = use_agent(monkeypatch, FakeAgent(answer="Plan for Goa"))
    resp = client.post("/query", json={"question": "Plan a 3-day trip to Goa"})
    assert resp.status_code == 200
    assert resp.json() == {"answer": "Plan for Goa"}
    sent = fake.calls[0]["messages"]
    assert len(sent) == 1 and sent[0].content == "Plan a 3-day trip to Goa"


def test_query_error_is_clean_500_without_leaking_details(client, monkeypatch):
    use_agent(monkeypatch, FakeAgent(error=RuntimeError("secret-key-abc rejected")))
    resp = client.post("/query", json={"question": "Plan a trip"})
    assert resp.status_code == 500
    body = resp.json()
    assert "RuntimeError" in body["error"]
    assert "secret-key-abc" not in body["error"]


def test_query_requires_question(client, monkeypatch):
    use_agent(monkeypatch, FakeAgent())
    assert client.post("/query", json={}).status_code == 422


def test_cors_allows_streamlit_origin(client):
    resp = client.options(
        "/query",
        headers={"Origin": "https://example.streamlit.app", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") in ("*", "https://example.streamlit.app")


# ================================================================ agent graph

def test_graph_builds_with_all_tools_offline(monkeypatch):
    class FakeLLM:
        def bind_tools(self, bound):
            self.tools = bound
            return self

    monkeypatch.setattr(agent, "load_llm", lambda provider: FakeLLM())
    app = agent.build_agent("groq")
    assert {"agent", "tools"} <= set(app.get_graph().nodes)


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError, match="Unknown MODEL_PROVIDER"):
        agent.load_llm("mystery")
