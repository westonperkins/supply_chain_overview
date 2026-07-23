// Country hybrid rule per user directive:
//   - has outbound supply edges OR host_count >= HOST_THRESHOLD  → first-class node
//   - else → collapse to a flag badge on the host company/facility
//
// Rationale: a country hosting many nodes is itself a concentration signal
// worth showing. A country hosting 1 chokepoint is context, not a data point,
// and its 0.0 severity would render as "safe" — so it lives as metadata.
//
// Pass G — decouple badge emission from the first-class decision. The two
// were coupled in the ELSE branch below, so promoting a country to
// first-class silently suppressed badges on every node it hosted (Lam
// Research had no USA tag while ASML had a Netherlands one). The badge
// is metadata about the HOST; whether the COUNTRY renders as its own
// node is a layout decision. Populate `badgeByHost` for every host,
// regardless of the country's first-class status. `firstClassCountries`
// and `HOST_THRESHOLD` are the layout rule and are deliberately
// untouched.
//
// Multi-country nodes: the badge shows the primary location (highest
// input_share `located_in`). The detail card lists all `located_in`
// relationships so the graph never claims a multinational lives in one
// country. Currently no node has multiple `located_in` edges; the
// primary-selection code path is exercised defensively.

import type { Node, Edge } from "../types";

const HOST_THRESHOLD = 3;

const SUPPLY_EDGE_TYPES = new Set([
  "mines",
  "refines",
  "supplies",
  "input_to",
  "component_of",
]);

// Node types eligible to carry a country badge. Minerals + products don't
// have a single location; countries obviously don't badge themselves.
const BADGE_ELIGIBLE_TYPES = new Set(["company", "facility"]);

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
  "country_region:germany":       "🇩🇪",
};

export interface BadgeDecisions {
  firstClassCountries: Set<string>;
  badgeByHost: Map<string, { flag: string; name: string }>;
}

export function decideCountryBadges(nodes: Node[], edges: Edge[]): BadgeDecisions {
  const hosts = new Map<string, string[]>();          // country_id -> [host_ids]
  const countriesWithSupply = new Set<string>();
  // For multi-country hosts, pick the highest input_share as primary.
  // {host_id: [{country_id, weight}]}
  const hostToCountries = new Map<string, Array<{ country: string; weight: number }>>();

  for (const e of edges) {
    if (e.type === "located_in" && e.target_id.startsWith("country_region:")) {
      if (!hosts.has(e.target_id)) hosts.set(e.target_id, []);
      hosts.get(e.target_id)!.push(e.source_id);
      if (!hostToCountries.has(e.source_id)) hostToCountries.set(e.source_id, []);
      hostToCountries.get(e.source_id)!.push({
        country: e.target_id,
        weight: e.input_share ?? 1.0,
      });
    }
    if (e.source_id.startsWith("country_region:") && SUPPLY_EDGE_TYPES.has(e.type)) {
      countriesWithSupply.add(e.source_id);
    }
  }

  const firstClass = new Set<string>();
  for (const n of nodes) {
    if (n.type !== "country_region") continue;
    const hostList = hosts.get(n.id) ?? [];
    const hasSupply = countriesWithSupply.has(n.id);
    if (hasSupply || hostList.length >= HOST_THRESHOLD) {
      firstClass.add(n.id);
    }
    // Countries that don't clear either bar and have no hosts render as
    // nothing; that's fine.
  }

  // Pass G — populate badgeByHost for EVERY eligible host, regardless of
  // whether the country is first-class. Decoupled from the layout rule
  // above per spec §Part 1.
  const badges = new Map<string, { flag: string; name: string }>();
  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  for (const [hostId, countries] of hostToCountries) {
    const host = nodeById.get(hostId);
    if (!host || !BADGE_ELIGIBLE_TYPES.has(host.type)) continue;
    // Primary location = highest input_share; tie-break by country id
    // for deterministic rendering.
    const primary = [...countries].sort(
      (a, b) => (b.weight - a.weight) || a.country.localeCompare(b.country),
    )[0];
    const country = nodeById.get(primary.country);
    if (!country) continue;
    const flag = COUNTRY_FLAGS[primary.country] ?? "🌍";
    badges.set(hostId, { flag, name: country.name });
  }

  return { firstClassCountries: firstClass, badgeByHost: badges };
}
