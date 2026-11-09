"""The trip-planning agent: an LLM with tools, looping until it stops calling them."""
import logging
import os

from dotenv import load_dotenv
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from prompt import SYSTEM_PROMPT
from tools import ALL_TOOLS

logger = logging.getLogger(__name__)

# Default model per provider; override with MODEL_NAME.
DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "openai": "gpt-4o-mini",
}


def load_llm(provider: str):
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"Unknown MODEL_PROVIDER {provider!r}; use one of {list(DEFAULT_MODELS)}")
    model = os.getenv("MODEL_NAME") or DEFAULT_MODELS[provider]
    logger.info(f"Using {provider} model {model}")
    if provider == "groq":
        from langchain_groq import ChatGroq

        # Retries 429 rate-limit errors with backoff (Groq's free tier has a low tokens/minute cap).
        return ChatGroq(model=model, api_key=os.getenv("GROQ_API_KEY"), max_retries=6)

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model, api_key=os.getenv("OPENAI_API_KEY"))


def build_agent(provider: str | None = None):
    """Compile the LangGraph agent. Provider comes from MODEL_PROVIDER (default: groq)."""
    load_dotenv()
    llm = load_llm(provider or os.getenv("MODEL_PROVIDER", "groq")).bind_tools(ALL_TOOLS)

    def agent(state: MessagesState):
        response = llm.invoke([SYSTEM_PROMPT, *state["messages"]])
        for call in getattr(response, "tool_calls", None) or []:
            logger.info(f"🔥 TOOL CALL: {call['name']}({call['args']})")
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)  # -> "tools" on tool calls, otherwise END
    graph.add_edge("tools", "agent")
    logger.info(f"Agent ready with {len(ALL_TOOLS)} tools")
    return graph.compile()
