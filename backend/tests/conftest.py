"""pytest fixtures — every test runs against a frozen snapshot in
`fixtures/`, never the live graph, never the network. See the test-suite
build spec for why.
"""
import sys
from pathlib import Path

# Make `app` importable when pytest is invoked from anywhere.
BACKEND_ROOT = Path(__file__).parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from app.graph import SupplyChainGraph
from app.narration import NarrationBuilder, NarrationConfig
from app.scoring import ScoringConfig, propagate_event, refresh_all_derived

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def config() -> ScoringConfig:
    return ScoringConfig.load(FIXTURES / "scoring.yaml")


@pytest.fixture(scope="session")
def narration_config() -> NarrationConfig:
    return NarrationConfig.load(FIXTURES / "narration.yaml")


@pytest.fixture(scope="session")
def graph(config: ScoringConfig) -> SupplyChainGraph:
    g = SupplyChainGraph.from_dir(FIXTURES, domain="ai")
    refresh_all_derived(g, config)
    for event in g.events.values():
        propagate_event(event, g, config)
    return g


@pytest.fixture(scope="session")
def narration_builder(
    graph: SupplyChainGraph, narration_config: NarrationConfig
) -> NarrationBuilder:
    return NarrationBuilder(narration_config, graph)
