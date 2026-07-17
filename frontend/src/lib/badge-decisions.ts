// Country hybrid rule per user directive:
//   - has outbound supply edges OR host_count >= HOST_THRESHOLD  → first-class node
//   - else → collapse to a flag badge on the host company/facility
//
// Rationale: a country hosting many nodes is itself a concentration signal
// worth showing. A country hosting 1 chokepoint is context, not a data point,
// and its 0.0 severity would render as "safe" — so it lives as metadata.

import type { Node, Edge } from "../types";

const HOST_THRESHOLD = 3;

const SUPPLY_EDGE_TYPES = new Set([
  "mines",
  "refines",
  "supplies",
  "input_to",
  "component_of",
]);

// Regional-indicator flag emojis. Kachin has no country flag — waving flag glyph.
export const COUNTRY_FLAGS: Record<string, string> = {
  "country_region:china":         "🇨🇳",
  "country_region:taiwan":        "🇹🇼",
  "country_region:usa":           "🇺🇸",
  "country_region:netherlands":   "🇳🇱",
  "country_region:south_korea":   "🇰🇷",
  "country_region:japan":         "🇯🇵",
  "country_region:myanmar":       "🇲🇲",
  "country_region:kachin":        "⚑",
  "country_region:malaysia":      "🇲🇾",
  "country_region:australia":     "🇦🇺",
  "country_region:brazil":        "🇧🇷",
  "country_region:chile":         "🇨🇱",
  "country_region:drc":           "🇨🇩",
  "country_region:peru":          "🇵🇪",
  "country_region:canada":        "🇨🇦",
};

export interface BadgeDecisions {
  firstClassCountries: Set<string>;
  badgeByHost: Map<string, { flag: string; name: string }>;
}

export function decideCountryBadges(nodes: Node[], edges: Edge[]): BadgeDecisions {
  const hosts = new Map<string, string[]>();          // country_id -> [host_ids]
  const countriesWithSupply = new Set<string>();

  for (const e of edges) {
    if (e.type === "located_in" && e.target_id.startsWith("country_region:")) {
      if (!hosts.has(e.target_id)) hosts.set(e.target_id, []);
      hosts.get(e.target_id)!.push(e.source_id);
    }
    if (e.source_id.startsWith("country_region:") && SUPPLY_EDGE_TYPES.has(e.type)) {
      countriesWithSupply.add(e.source_id);
    }
  }

  const firstClass = new Set<string>();
  const badges = new Map<string, { flag: string; name: string }>();

  for (const n of nodes) {
    if (n.type !== "country_region") continue;
    const hostList = hosts.get(n.id) ?? [];
    const hasSupply = countriesWithSupply.has(n.id);

    if (hasSupply || hostList.length >= HOST_THRESHOLD) {
      firstClass.add(n.id);
    } else if (hostList.length > 0) {
      const flag = COUNTRY_FLAGS[n.id] ?? "🌍";
      for (const hostId of hostList) {
        badges.set(hostId, { flag, name: n.name });
      }
    }
    // else: country has no supply AND no hosts → not rendered at all
  }

  return { firstClassCountries: firstClass, badgeByHost: badges };
}
