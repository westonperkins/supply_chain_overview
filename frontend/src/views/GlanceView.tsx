import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useReactFlow,
  type Node as RFNode,
  type Edge as RFEdge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { Node, Edge } from "../types";
import { META_LAYERS, type MetaLayerId } from "../lib/render-config";
import { decideCountryBadges } from "../lib/badge-decisions";
import { computeFullLayout } from "../lib/full-layout";
import { HoverContext, type HoverState } from "../lib/hover-context";
import { ChokepointNode } from "./glance/ChokepointNode";
import { CountryNode } from "./glance/CountryNode";
import { SummaryNode } from "./glance/SummaryNode";
import { ColumnLabelNode } from "./glance/ColumnLabelNode";

const nodeTypes = {
  chokepoint: ChokepointNode as unknown as React.ComponentType<any>,
  country: CountryNode as unknown as React.ComponentType<any>,
  summary: SummaryNode as unknown as React.ComponentType<any>,
  columnLabel: ColumnLabelNode as unknown as React.ComponentType<any>,
};

const SUPPLY_FEED_TYPES = new Set(["mines", "refines"]);
const OWNERSHIP_TYPES = new Set(["operates"]);

interface EdgeStyle {
  strokeWidth: number;
  stroke: string;
  opacity: number;
  strokeDasharray?: string;
}

function edgeStyle(weight: number, edgeType: string): EdgeStyle {
  if (OWNERSHIP_TYPES.has(edgeType)) {
    return {
      strokeWidth: 1.5,
      stroke: "var(--edge-supply-muted)",
      strokeDasharray: "6 4",
      opacity: 0.55,
    };
  }
  if (SUPPLY_FEED_TYPES.has(edgeType)) {
    return {
      strokeWidth: Math.max(0.6, (1 + weight * 6) * 0.35),
      stroke: "var(--edge-supply-muted)",
      opacity: 0.65,
    };
  }
  return {
    strokeWidth: 1 + weight * 6,
    stroke:
      weight >= 0.7 ? "var(--edge-strong)"
      : weight >= 0.3 ? "var(--edge-med)"
      :                 "var(--edge-weak)",
    opacity: 1,
  };
}

function markerFor(edgeType: string) {
  const muted = SUPPLY_FEED_TYPES.has(edgeType) || OWNERSHIP_TYPES.has(edgeType);
  return {
    type: MarkerType.ArrowClosed,
    color: muted ? "var(--edge-supply-muted)" : "var(--edge-med)",
    width: muted ? 8 : 12,
    height: muted ? 8 : 12,
  };
}

interface Props {
  nodes: Node[];
  edges: Edge[];
  onSelectNode?: (id: string) => void;
}

interface Highlight {
  nodes: Set<string>;
  edges: Set<string>;
}

function computeReachable(
  startId: string,
  edges: { id: string; source: string; target: string }[],
): Highlight {
  const highlightedNodes = new Set<string>([startId]);
  const highlightedEdges = new Set<string>();
  const outgoingByNode = new Map<string, typeof edges>();
  const incomingByNode = new Map<string, typeof edges>();
  for (const e of edges) {
    if (!outgoingByNode.has(e.source)) outgoingByNode.set(e.source, []);
    outgoingByNode.get(e.source)!.push(e);
    if (!incomingByNode.has(e.target)) incomingByNode.set(e.target, []);
    incomingByNode.get(e.target)!.push(e);
  }
  const dQueue: string[] = [startId];
  while (dQueue.length) {
    const cur = dQueue.shift()!;
    for (const e of outgoingByNode.get(cur) ?? []) {
      highlightedEdges.add(e.id);
      if (!highlightedNodes.has(e.target)) {
        highlightedNodes.add(e.target);
        dQueue.push(e.target);
      }
    }
  }
  const uQueue: string[] = [startId];
  while (uQueue.length) {
    const cur = uQueue.shift()!;
    for (const e of incomingByNode.get(cur) ?? []) {
      highlightedEdges.add(e.id);
      if (!highlightedNodes.has(e.source)) {
        highlightedNodes.add(e.source);
        uQueue.push(e.source);
      }
    }
  }
  return { nodes: highlightedNodes, edges: highlightedEdges };
}

const LABEL_Y = -68;

function GlanceInternal({ nodes, edges, onSelectNode }: Props) {
  const [collapsed, setCollapsed] = useState<Set<MetaLayerId>>(new Set(["chips"]));
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const rf = useReactFlow();
  const flowWrapRef = useRef<HTMLDivElement>(null);

  const toggleLayer = (id: MetaLayerId) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const badges = useMemo(() => decideCountryBadges(nodes, edges), [nodes, edges]);
  const layout = useMemo(
    () => computeFullLayout(nodes, edges, badges, collapsed),
    [nodes, edges, badges, collapsed],
  );

  useEffect(() => {
    const t = setTimeout(() => rf.fitView({ padding: 0.1, duration: 260 }), 30);
    return () => clearTimeout(t);
  }, [collapsed, rf]);

  const highlight = useMemo<Highlight | null>(() => {
    if (!hoveredId) return null;
    return computeReachable(hoveredId, layout.flowEdges);
  }, [hoveredId, layout.flowEdges]);

  // -------------------------------------------------------------------- //
  // STABLE flowNodes / flowEdges — no hover dependency, ever.            //
  //                                                                      //
  // Previous bug: including `hoveredId` / `highlight` in the deps here   //
  // rebuilt the entire node + edge arrays on every mouse-move. React     //
  // Flow saw new object identities, re-mounted every node/edge, and the  //
  // remount thrash showed up as a rapid flash → occasional total vanish. //
  //                                                                      //
  // Fix: these arrays only change when the LAYOUT changes (collapse /    //
  // expand, or the underlying graph). Hover is applied to the DOM in a   //
  // separate useEffect below, without React state churn.                 //
  // -------------------------------------------------------------------- //
  const flowNodes: RFNode[] = useMemo(() => {
    const contentNodes = layout.flowNodes.map((fn) => ({
      id: fn.id,
      type: fn.kind,
      position: { x: fn.x, y: fn.y },
      data: fn.data,
      draggable: false,
      selectable: fn.kind !== "country",
    }));
    const labelNodes = layout.columnHeaders.map((h, i) => ({
      id: `label:${i}:${h.metaLayerId}:${h.label}`,
      type: "columnLabel",
      position: { x: h.x, y: LABEL_Y },
      data: {
        isFirstOfMeta: h.isFirstOfMeta,
        isCollapsedSummary: h.isCollapsedSummary,
        metaLabel: h.metaLayerLabel,
        subLabel: h.label,
        width: h.width,
      },
      draggable: false,
      selectable: false,
    }));
    return [...labelNodes, ...contentNodes];
  }, [layout.flowNodes, layout.columnHeaders]);

  const flowEdges: RFEdge[] = useMemo(
    () =>
      layout.flowEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        style: edgeStyle(e.weight, e.edgeType),
        markerEnd: markerFor(e.edgeType),
      })),
    [layout.flowEdges],
  );

  // -------------------------------------------------------------------- //
  // Nodes get their hover styling via a React context — see the custom  //
  // node components (ChokepointNode / CountryNode / SummaryNode). This  //
  // keeps the flowNodes ARRAY identity-stable while still letting each  //
  // node re-render its own className when hover changes.                //
  //                                                                     //
  // Edges are managed internally by React Flow, so hover styling goes   //
  // via imperative DOM classes (edges expose data-id on their <g>).     //
  // -------------------------------------------------------------------- //
  const hoverValue: HoverState = useMemo(
    () => ({
      hoveredId,
      trailNodes: highlight ? highlight.nodes : null,
      trailEdges: highlight ? highlight.edges : null,
    }),
    [hoveredId, highlight],
  );

  useEffect(() => {
    const wrap = flowWrapRef.current;
    if (!wrap) return;
    const raf = requestAnimationFrame(() => {
      const edgeEls = wrap.querySelectorAll<Element>(".react-flow__edge");
      edgeEls.forEach((el) => {
        const id = (el as HTMLElement).dataset.id ?? "";
        if (!highlight) {
          el.classList.remove("is-dimmed-edge", "is-lit-edge");
        } else if (highlight.edges.has(id)) {
          el.classList.add("is-lit-edge");
          el.classList.remove("is-dimmed-edge");
        } else {
          el.classList.add("is-dimmed-edge");
          el.classList.remove("is-lit-edge");
        }
      });
    });
    return () => cancelAnimationFrame(raf);
  }, [hoveredId, highlight, layout.flowEdges]);

  return (
    <div className="glance-container">
      <div className="glance-header">
        <div className="glance-header-title">Level 0 — layered supply-chain flow · {nodes.length} nodes</div>
        <div className="glance-legend">
          <span className="glance-legend-item"><span className="tier-dot critical" /> critical</span>
          <span className="glance-legend-item"><span className="tier-dot high" /> high</span>
          <span className="glance-legend-item"><span className="tier-dot moderate" /> moderate</span>
          <span className="glance-legend-item"><span className="tier-dot none" /> none</span>
          <span className="glance-legend-item glance-legend-supply">
            <span className="tier-dot supply" /> supply source
          </span>
          <span className="glance-legend-shapes">
            <span className="shape-sample" title="mineral">⛏ mineral</span>
            <span className="shape-sample" title="product">◆ product</span>
            <span className="shape-sample" title="company">▭ company</span>
            <span className="shape-sample" title="facility">🏭 facility</span>
          </span>
        </div>
      </div>

      <div className="glance-layer-controls">
        {META_LAYERS.map((meta) => {
          const isCollapsed = collapsed.has(meta.id);
          return (
            <button
              key={meta.id}
              className={`layer-toggle ${isCollapsed ? "is-collapsed" : "is-expanded"}`}
              onClick={() => toggleLayer(meta.id)}
              title={`${isCollapsed ? "Expand" : "Collapse"} ${meta.label}`}
            >
              <span className="layer-toggle-icon">{isCollapsed ? "⊕" : "⊖"}</span>
              <span className="layer-toggle-label">{meta.label}</span>
            </button>
          );
        })}
        <div className="glance-hover-hint">
          hover a node → highlight its full up + downstream chain
        </div>
      </div>

      <div className="glance-flow-wrap" ref={flowWrapRef}>
        <HoverContext.Provider value={hoverValue}>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.1 }}
          minZoom={0.15}
          maxZoom={2.5}
          nodesDraggable={false}
          nodesConnectable={false}
          panOnDrag
          panOnScroll
          zoomOnScroll={false}
          zoomOnPinch
          proOptions={{ hideAttribution: true }}
          onNodeMouseEnter={(_, node) => {
            if (node.type !== "columnLabel") setHoveredId(node.id);
          }}
          onNodeMouseLeave={(_, node) => {
            // Only clear if we're leaving the currently-hovered node; going
            // node → adjacent-node may fire leave AFTER the new enter, and
            // we don't want that to erase the freshly-set hover.
            setHoveredId((current) => (current === node.id ? null : current));
          }}
          onNodeClick={(_, node) => {
            if (
              node.type !== "summary" &&
              node.type !== "country" &&
              node.type !== "columnLabel"
            ) {
              onSelectNode?.(node.id);
            }
          }}
        >
          <Background gap={24} size={1} color="var(--border)" />
          <Controls showInteractive={false} />
        </ReactFlow>
        </HoverContext.Provider>
      </div>
    </div>
  );
}

export default function GlanceView(props: Props) {
  return (
    <ReactFlowProvider>
      <GlanceInternal {...props} />
    </ReactFlowProvider>
  );
}
