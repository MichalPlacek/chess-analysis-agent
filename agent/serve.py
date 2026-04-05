"""Entry point for launching the FastAPI/LangServe server."""
import uvicorn


def main() -> None:
    uvicorn.run("server:app", reload=True)
