import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from agent import build_agent

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("trip_planner")

app = FastAPI(title="AI Trip Planner")

# Comma-separated list, e.g. "https://my-app.streamlit.app". Defaults to any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


@lru_cache(maxsize=1)
def get_agent():
    """Build the agent once, on the first request, and reuse it."""
    return build_agent()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query_travel_agent(query: QueryRequest):
    # Sync handler: FastAPI runs it in a threadpool, so the slow LLM call doesn't block the server.
    logger.info(f"Query: {query.question!r}")
    try:
        output = get_agent().invoke({"messages": [HumanMessage(content=query.question)]})
        return {"answer": output["messages"][-1].content}
    except Exception as e:
        logger.exception("Agent run failed")
        return JSONResponse(
            status_code=500,
            content={"error": f"The planner hit an error ({type(e).__name__}). Check the backend logs for details."},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
