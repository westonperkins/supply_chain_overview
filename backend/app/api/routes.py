from fastapi import APIRouter, HTTPException

from ..graph import SupplyChainGraph
from ..narration import NarrationBuilder, NarrationConfig
from ..scoring import ScoringConfig, propagate_event


def build_router(
    graph: SupplyChainGraph,
    config: ScoringConfig,
    narration: NarrationBuilder,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health():
        return {"status": "ok", "nodes": len(graph.nodes), "edges": len(graph.edges), "events": len(graph.events)}

    @router.get("/nodes")
    def list_nodes():
        return [n.model_dump() for n in graph.nodes.values()]

    @router.get("/nodes/{node_id}")
    def get_node(node_id: str):
        node = graph.nodes.get(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"unknown node: {node_id}")
        return node.model_dump()

    @router.get("/nodes/{node_id}/upstream")
    def node_upstream(node_id: str):
        if node_id not in graph.nodes:
            raise HTTPException(status_code=404, detail=f"unknown node: {node_id}")
        return [e.model_dump() for e in graph.in_edges(node_id)]

    @router.get("/nodes/{node_id}/downstream")
    def node_downstream(node_id: str):
        if node_id not in graph.nodes:
            raise HTTPException(status_code=404, detail=f"unknown node: {node_id}")
        return [e.model_dump() for e in graph.out_edges(node_id)]

    @router.get("/edges")
    def list_edges():
        return [e.model_dump() for e in graph.edges.values()]

    @router.get("/edges/{edge_id}")
    def get_edge(edge_id: str):
        edge = graph.edges.get(edge_id)
        if edge is None:
            raise HTTPException(status_code=404, detail=f"unknown edge: {edge_id}")
        return edge.model_dump()

    @router.get("/events")
    def list_events():
        return [e.model_dump() for e in graph.events.values()]

    @router.get("/events/{event_id}")
    def get_event(event_id: str):
        event = graph.events.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail=f"unknown event: {event_id}")
        return event.model_dump()

    @router.get("/events/{event_id}/cascade")
    def event_cascade(event_id: str):
        event = graph.events.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail=f"unknown event: {event_id}")
        # Compute fresh each call so config edits are picked up.
        propagate_event(event, graph, config)
        return event.model_dump()

    @router.get("/config/scoring")
    def scoring_config():
        return config.raw

    @router.get("/nodes/{node_id}/narration")
    def node_narration(node_id: str):
        try:
            return narration.build(node_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"unknown node: {node_id}")

    return router
