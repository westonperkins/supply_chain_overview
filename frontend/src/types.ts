// Frontend mirrors of the backend Pydantic schema. Kept intentionally lean —
// only fields the current UI reads.

export type NodeType = "mineral" | "company" | "facility" | "country_region" | "product";
export type Layer = "materials" | "chips" | "power" | "data_centers";
export type ChokepointTier = "critical" | "high" | "moderate" | "none" | "unscored";
export type Confidence = "hard" | "estimate" | "inference";

export interface SourcedValue<T = unknown> {
  value: T;
  confidence: Confidence;
  source_note?: string | null;
}

export interface StaticFields {
  scale?: SourcedValue<{ value: number; unit: string }> | null;
  substitutability?: SourcedValue<number> | null;
  lead_time_years?: SourcedValue<number> | null;
  bottleneck_type?: string | null;
  financial_cushion?: SourcedValue<number> | null;
  notes?: string | null;
}

export interface DynamicFields {
  price?: number | null;
  price_ex_china?: number | null;
  price_spread?: number | null;
  market_cap?: number | null;
  market_share?: number | null;
  inbound_hhi?: number | null;
  outbound_criticality?: number | null;
  concentration?: number | null;
  // Pass D — structural (never moved by events) vs live (event-adjusted).
  // With no active events, baseline_* == current_* by definition.
  // Glance colours by baseline_tier this pass; current_tier waits for the
  // news-ingestion pass. The legacy per-node tier field was renamed to
  // baseline_tier in Pass D; served JSON no longer carries the old name.
  baseline_severity?: number | null;
  baseline_tier?: ChokepointTier | null;
  current_severity?: number | null;
  current_tier?: ChokepointTier | null;
  // Provenance flag attached by cascade — true if any contribution to
  // current_severity came from an unscored-origin event. Ranking policy
  // (how the frontend uses this) is a future news-ingestion concern.
  current_severity_has_unscored_origin?: boolean;
  // Names the required static axes that were missing when the engine
  // refused to score this node (Pass A unscored mode). Empty/null when
  // the node scored. Powers the "Why this isn't scored" narration.
  scored_on_default_axes?: string[] | null;
  derived_shares?: Record<string, Record<string, number>> | null;
  recent_event_ids: string[];
  last_updated?: string | null;
}

// Pass G Part 3 — display-tier guard.
//
// Pass H's cascade fix writes current_severity on unscored nodes and
// re-derives current_tier from it — so a node with
// baseline_severity === null can now carry current_tier: "none" (green).
// Any frontend colour/class resolution MUST use this helper, not raw
// current_tier / baseline_tier reads, so a future current_tier colouring
// mode cannot silently paint an unscored node green even if the backend
// invariant "current_tier stays unscored when baseline_tier is unscored"
// hasn't landed. Applies to every tier→colour path: ChokepointNode,
// SummaryNode counts, Dashboard filters + badges.
export function displayTier(node: Node): ChokepointTier {
  if (node.dynamic.baseline_severity == null) return "unscored";
  return node.dynamic.baseline_tier ?? "unscored";
}

// The rendered narration payload from `/nodes/{id}/narration`.
export interface NarrationSection {
  key: string;
  title: string;
  body: string;
}
// Pass I / I.1 — structured glance payload built from real edges.
// The backend produces this so the frontend never composes prose or
// picks edges heuristically (the source of the "China supplies copper
// to TSMC" misread — no such path existed in the graph).
//
// Each breadcrumb step is one real graph edge. Each of `paths` is a
// full greedy max-weight walk seeded from a distinct first-hop edge —
// the diversity rule that forces fan-out to show.
export interface GlanceBreadcrumbStep {
  from: string;
  verb: string;   // authored in narration.yaml `edge_glance_verb`
  share: number;  // 0..1 effective edge weight
  to: string;
}
export interface GlanceSupplyLine {
  text: string;                     // authored, fully rendered
  target_id: string | null;
  verb: string | null;
  share: number | null;
  kind: "edge" | "overflow";
}
export interface GlanceStats {
  downstream_nodes: number;
  total_nodes: number;
  critical_reached: string[];       // node ids
  high_reached: string[];
  layers_crossed: number;
}
// Chip + section labels ALSO come from the backend so the frontend
// composes zero English — even the word "Supplies" lives in
// narration.yaml `glance_strip.section_labels`.
export interface GlanceLabels {
  sections: {
    supply_lines?: string;
    reach?: string;
    paths?: string;
  };
  chips: {
    trail_label?: string;
    critical_label?: string;
    high_label?: string;
    layers_label?: string;
  };
}
export interface Glance {
  summary: string | null;
  supply_lines: GlanceSupplyLine[];
  reach: string | null;
  paths: GlanceBreadcrumbStep[][];
  stats: GlanceStats;
  labels: GlanceLabels;
  acronyms: { term: string; expansion: string }[];
}
export interface Narration {
  node_id: string;
  headline: { name: string; role: string | null; tier: string };
  dominant_axis: string;
  sections: NarrationSection[];
  caveats: string[];
  acronyms: { term: string; expansion: string }[];
  glance: Glance;
}

export interface Node {
  id: string;
  type: NodeType;
  name: string;
  aliases: string[];
  domains: string[];
  layer?: Layer | null;
  sub_category?: string | null;
  description?: string | null;
  static: StaticFields;
  dynamic: DynamicFields;
}

export interface Edge {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
  input_share: number;               // preferred — source's share of target's supply
  output_share?: number | null;      // optional — target's share of source's output
  weight: number;                    // legacy alias for input_share; backend still serialises it
  supply_category?: string | null;   // only meaningful on `supplies` edges — see backend schema
  domains: string[];
  static: {
    notes?: string | null;
    confidence?: Confidence;
    source_note?: string | null;
    output_share_confidence?: Confidence | null;
    output_share_source_note?: string | null;
  };
}

export interface EntityMatch {
  node_id: string;
  confidence: number;
  match_type: string;
}

export interface CascadeStep {
  node_id: string;
  hop: number;
  severity_at_node: number;
  edge_path: string[];
}

export interface Event {
  id: string;
  timestamp: string;
  headline: string;
  summary?: string | null;
  entities_matched: EntityMatch[];
  axes_impact: {
    concentration_delta: number;
    substitutability_delta: number;
    lead_time_delta: number;
  };
  severity?: number | null;
  cascade: CascadeStep[];
  tags: string[];
  notes?: string | null;
}
