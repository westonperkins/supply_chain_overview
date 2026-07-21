from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import build_router
from .graph import SupplyChainGraph
from .narration import NarrationBuilder, NarrationConfig
from .scoring import ScoringConfig, propagate_event, refresh_all_derived


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
CONFIG_PATH = REPO_ROOT / "config" / "scoring.yaml"
NARRATION_CONFIG_PATH = REPO_ROOT / "config" / "narration.yaml"


def create_app() -> FastAPI:
    app = FastAPI(title="AI Supply Chain Terminal", version="0.1.0")

    # Local dev only — Vite defaults to 5173.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    graph = SupplyChainGraph.from_dir(DATA_DIR, domain="ai")
    config = ScoringConfig.load(CONFIG_PATH)

    # Refresh derived fields at startup: shares from edges, HHI, baseline
    # severity, chokepoint_tier. Also pre-score events so a plain /events call
    # returns useful data without requiring the cascade endpoint.
    refresh_all_derived(graph, config)
    for event in graph.events.values():
        propagate_event(event, graph, config)

    narration_config = NarrationConfig.load(NARRATION_CONFIG_PATH)
    narration = NarrationBuilder(narration_config, graph)

    app.include_router(build_router(graph, config, narration))
    return app


app = create_app()
