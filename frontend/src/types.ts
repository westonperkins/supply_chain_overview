// Frontend mirrors of the backend Pydantic schema. Kept intentionally lean —
// only fields the current UI reads.

export type NodeType = "mineral" | "company" | "facility" | "country_region" | "product";
export type Layer = "materials" | "chips" | "power" | "data_centers";
export type ChokepointTier = "critical" | "high" | "moderate" | "none";
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
  current_severity?: number | null;
  chokepoint_tier?: ChokepointTier | null;
  derived_shares?: Record<string, Record<string, number>> | null;
  recent_event_ids: string[];
  last_updated?: string | null;
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
  weight: number;
  domains: string[];
  static: { notes?: string | null; confidence?: Confidence; source_note?: string | null };
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
