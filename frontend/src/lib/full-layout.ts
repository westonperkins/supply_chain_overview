// Computes the full 63-node Glance layout given a collapse state.
//
//   - Assigns each node to a meta-layer + sub-column.
//   - For expanded meta-layers: renders every sub-column that has nodes.
//   - For collapsed meta-layers: renders one summary node at the layer position.
//   - Rewrites edge endpoints when either end is in a collapsed layer,
//     deduping to the maximum weight per (source, target) pair.

import type { Node, Edge } from "../types";
import {
  META_LAYERS,
  SUB_COLUMNS,
  classifyNode,
  metaLayerOf,
  type MetaLayerId,
} from "./render-config";
import type { BadgeDecisions } from "./badge-decisions";

const COL_WIDTH = 220;
// Wider gutter between columns (was 44) so parallel bezier edges have room to
// separate before they re-converge, easing the mid-graph tangle.
const COL_GAP = 82;
const NODE_HEIGHT = 106;
const NODE_STACK_GAP = 12;
const TOP_MARGIN = 40;

// Sources renders as a single column like every other category. Country cards
// are compact (flag + short name) and stack tightly, so a 13-row column
// remains comparable in height to the tallest chokepoint column.
const COUNTRY_HEIGHT = 40;
const COUNTRY_STACK_GAP = 6;
const SUMMARY_HEIGHT = 110;

// Only located_in is purely geographic metadata; operates is now a supply
// edge (see backend enums.py SUPPLY_EDGE_TYPES) so it renders in Glance with
// distinct styling to indicate ownership, not direct raw supply.
const STRUCTURAL_HIDDEN = new Set(["located_in"]);

const SOURCES_COL_ID = "src_countries";

export type FlowNodeKind = "chokepoint" | "country" | "summary";

export interface FlowNodePos {
  id: string;
  kind: FlowNodeKind;
  x: number;
  y: number;
  data: any;
}

export interface FlowEdgeSpec {
  id: string;
  source: string;
  target: string;
  weight: number;
  edgeType: string;
}

export interface ColumnHeader {
  x: number;
  width: number;
  label: string;
  metaLayerId: MetaLayerId;
  metaLayerLabel: string;
  isFirstOfMeta: boolean;
  isCollapsedSummary: boolean;
}

export interface LayoutResult {
  flowNodes: FlowNodePos[];
  flowEdges: FlowEdgeSpec[];
  columnHeaders: ColumnHeader[];
  totalWidth: number;
  totalHeight: number;
}

export function computeFullLayout(
  nodes: Node[],
  edges: Edge[],
  badges: BadgeDecisions,
  collapsedLayers: Set<MetaLayerId>,
): LayoutResult {
  // 1) Classify visible nodes into (sub-column, meta-layer).
  const nodeSubColumn = new Map<string, string>();
  const nodeMetaLayer = new Map<string, MetaLayerId>();

  const isVisibleCountry = (n: Node) =>
    n.type !== "country_region" || badges.firstClassCountries.has(n.id);

  for (const n of nodes) {
    if (!isVisibleCountry(n)) continue;
    const sc = classifyNode(n);
    if (!sc) continue;
    nodeSubColumn.set(n.id, sc.id);
    nodeMetaLayer.set(n.id, sc.metaLayer);
  }

  // 2) Determine which columns are rendered, their X positions, and their
  //    widths. Sources uses a wider column to fit the 2-col mini-grid.
  const subColX = new Map<string, number>();
  const subColWidth = new Map<string, number>();
  const summaryLayerX = new Map<MetaLayerId, number>();
  const columnHeaders: ColumnHeader[] = [];
  let cursorX = 0;

  for (const meta of META_LAYERS) {
    if (collapsedLayers.has(meta.id)) {
      const x = cursorX;
      summaryLayerX.set(meta.id, x);
      columnHeaders.push({
        x,
        width: COL_WIDTH,
        label: meta.label,
        metaLayerId: meta.id,
        metaLayerLabel: meta.label,
        isFirstOfMeta: true,
        isCollapsedSummary: true,
      });
      cursorX += COL_WIDTH + COL_GAP;
      continue;
    }
    const subCols = SUB_COLUMNS.filter((sc) => sc.metaLayer === meta.id);
    let firstOfMeta = true;
    for (const sc of subCols) {
      const hasNodes = Array.from(nodeSubColumn.values()).includes(sc.id);
      if (!hasNodes) continue;
      const x = cursorX;
      subColX.set(sc.id, x);
      subColWidth.set(sc.id, COL_WIDTH);
      columnHeaders.push({
        x,
        width: COL_WIDTH,
        label: sc.label,
        metaLayerId: meta.id,
        metaLayerLabel: meta.label,
        isFirstOfMeta: firstOfMeta,
        isCollapsedSummary: false,
      });
      firstOfMeta = false;
      cursorX += COL_WIDTH + COL_GAP;
    }
  }
  const totalWidth = cursorX;

  // 3) Group visible nodes by sub-column and sort each column by severity.
  const flowNodes: FlowNodePos[] = [];
  const summariesToRender = new Set<MetaLayerId>();
  const bySubCol = new Map<string, Node[]>();

  for (const n of nodes) {
    if (!isVisibleCountry(n)) continue;
    const scid = nodeSubColumn.get(n.id);
    if (!scid) continue;
    const metaId = nodeMetaLayer.get(n.id)!;
    if (collapsedLayers.has(metaId)) {
      summariesToRender.add(metaId);
      continue;
    }
    if (!bySubCol.has(scid)) bySubCol.set(scid, []);
    bySubCol.get(scid)!.push(n);
  }

  for (const colNodes of bySubCol.values()) {
    colNodes.sort(
      (a, b) => (b.dynamic.current_severity ?? 0) - (a.dynamic.current_severity ?? 0),
    );
  }

  // 4) Compute each column's *effective height* and the common midline.
  function columnHeight(scid: string, count: number): number {
    const pitch = scid === SOURCES_COL_ID
      ? COUNTRY_HEIGHT + COUNTRY_STACK_GAP
      : NODE_HEIGHT + NODE_STACK_GAP;
    const gap = scid === SOURCES_COL_ID ? COUNTRY_STACK_GAP : NODE_STACK_GAP;
    return Math.max(0, count * pitch - gap);
  }

  let maxColHeight = SUMMARY_HEIGHT;
  for (const [scid, colNodes] of bySubCol) {
    const h = columnHeight(scid, colNodes.length);
    if (h > maxColHeight) maxColHeight = h;
  }
  const centerY = TOP_MARGIN + maxColHeight / 2;

  // 5) Position downstream columns first (severity sort), then barycentric-
  //    order Sources against those positions. This is the standard fix for
  //    crossing edges out of a wide source layer: each country lands near the
  //    mean vertical position of the minerals it feeds, so single-mineral
  //    countries sit right beside their target and diagonals don't fan across
  //    the whole column.
  const nodeY = new Map<string, number>();

  for (const [scid, colNodes] of bySubCol) {
    if (scid === SOURCES_COL_ID) continue;
    const h = columnHeight(scid, colNodes.length);
    const startY = centerY - h / 2;
    const rowPitch = NODE_HEIGHT + NODE_STACK_GAP;
    const x = subColX.get(scid)!;
    colNodes.forEach((n, i) => {
      const y = startY + i * rowPitch;
      nodeY.set(n.id, y);
      flowNodes.push({
        id: n.id,
        kind: n.type === "country_region" ? "country" : "chokepoint",
        x,
        y,
        data: { node: n, badge: badges.badgeByHost.get(n.id) },
      });
    });
  }

  // Sources: barycentric sort by mean Y of downstream mines/refines targets.
  if (bySubCol.has(SOURCES_COL_ID)) {
    const srcNodes = bySubCol.get(SOURCES_COL_ID)!;
    const barycenter = new Map<string, number>();

    for (const country of srcNodes) {
      const targetYs: number[] = [];
      for (const e of edges) {
        if (e.source_id !== country.id) continue;
        if (e.type !== "mines" && e.type !== "refines") continue;
        const y = nodeY.get(e.target_id);
        if (y !== undefined) targetYs.push(y);
      }
      // Countries with no positioned downstream sort to the center.
      const bary = targetYs.length
        ? targetYs.reduce((s, y) => s + y, 0) / targetYs.length
        : centerY;
      barycenter.set(country.id, bary);
    }

    srcNodes.sort((a, b) => {
      const ba = barycenter.get(a.id) ?? centerY;
      const bb = barycenter.get(b.id) ?? centerY;
      // Break ties by severity so ordering is stable.
      if (ba !== bb) return ba - bb;
      return (b.dynamic.current_severity ?? 0) - (a.dynamic.current_severity ?? 0);
    });

    const h = columnHeight(SOURCES_COL_ID, srcNodes.length);
    const startY = centerY - h / 2;
    const rowPitch = COUNTRY_HEIGHT + COUNTRY_STACK_GAP;
    const x = subColX.get(SOURCES_COL_ID)!;
    srcNodes.forEach((n, i) => {
      flowNodes.push({
        id: n.id,
        kind: "country",
        x,
        y: startY + i * rowPitch,
        data: { node: n, badge: badges.badgeByHost.get(n.id) },
      });
    });
  }

  // Summary nodes: centered around the same midline as full columns.
  // Pass F — `unscored` is a first-class bucket, distinct from `none`.
  // worstTier walks scored tiers only (unscored is not "worse" or "better"
  // than a scored tier; it's a data-absence category), so the summary
  // outline reflects worst SCORED reading in the layer; unscored count
  // ships in tierCounts for the histogram to render its own bucket.
  const tierOrder: Array<"critical" | "high" | "moderate" | "none"> = [
    "critical",
    "high",
    "moderate",
    "none",
  ];
  for (const metaId of summariesToRender) {
    const x = summaryLayerX.get(metaId)!;
    const meta = META_LAYERS.find((m) => m.id === metaId)!;
    const inLayer = nodes.filter((n) => {
      if (!isVisibleCountry(n)) return false;
      return metaLayerOf(n) === metaId;
    });
    const tierCounts = { critical: 0, high: 0, moderate: 0, none: 0, unscored: 0 };
    let worstTier: "critical" | "high" | "moderate" | "none" = "none";
    for (const n of inLayer) {
      const t = (n.dynamic.baseline_tier ?? "unscored") as keyof typeof tierCounts;
      tierCounts[t]++;
      if (t !== "unscored" && tierOrder.indexOf(t) < tierOrder.indexOf(worstTier)) {
        worstTier = t;
      }
    }
    flowNodes.push({
      id: `summary:${metaId}`,
      kind: "summary",
      x,
      y: centerY - SUMMARY_HEIGHT / 2,
      data: {
        metaLayerId: metaId,
        label: meta.label,
        worstTier,
        tierCounts,
        count: inLayer.length,
      },
    });
  }

  // 4) Edges with collapse rewriting + dedupe.
  const rewritten = new Map<string, FlowEdgeSpec>();
  for (const e of edges) {
    if (STRUCTURAL_HIDDEN.has(e.type)) continue;

    let src = e.source_id;
    let tgt = e.target_id;

    // Skip if endpoint is a badge-collapsed country (not rendered as node).
    if (src.startsWith("country_region:") && !badges.firstClassCountries.has(src)) continue;
    if (tgt.startsWith("country_region:") && !badges.firstClassCountries.has(tgt)) continue;

    // Skip if endpoint doesn't classify (e.g., an unknown sub_category).
    const srcMeta = nodeMetaLayer.get(src);
    const tgtMeta = nodeMetaLayer.get(tgt);
    if (!srcMeta || !tgtMeta) continue;

    if (collapsedLayers.has(srcMeta)) src = `summary:${srcMeta}`;
    if (collapsedLayers.has(tgtMeta)) tgt = `summary:${tgtMeta}`;

    if (src === tgt) continue; // internal to a collapsed layer

    const key = `${src}->${tgt}`;
    const prev = rewritten.get(key);
    if (!prev || e.weight > prev.weight) {
      rewritten.set(key, {
        id: `e:${key}`,
        source: src,
        target: tgt,
        weight: e.weight,
        edgeType: e.type,
      });
    }
  }

  const flowEdges = Array.from(rewritten.values());
  const totalHeight = TOP_MARGIN * 2 + maxColHeight;

  return { flowNodes, flowEdges, columnHeaders, totalWidth, totalHeight };
}
