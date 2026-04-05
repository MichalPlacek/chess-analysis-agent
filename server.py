"""FastAPI + LangServe entry point for Chess Analysis Agent."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

from agent.graph import build_graph

app = FastAPI(
    title="Chess Analysis Agent",
    description="LangGraph-based chess position analysis API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

add_routes(app, build_graph(), path="/analyze")
