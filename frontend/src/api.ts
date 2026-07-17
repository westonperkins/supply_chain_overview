import type { Edge, Event, Node } from "./types";

const BASE = "http://127.0.0.1:8000";

async function j<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json() as Promise<T>;
}

export const api = {
  nodes: () => j<Node[]>("/nodes"),
  node: (id: string) => j<Node>(`/nodes/${encodeURIComponent(id)}`),
  edges: () => j<Edge[]>("/edges"),
  events: () => j<Event[]>("/events"),
  eventCascade: (id: string) => j<Event>(`/events/${encodeURIComponent(id)}/cascade`),
};

// Add weight to Edge (Edge type in types.ts already has it — this is a no-op
// re-export point in case we want to enrich later).
