// Full-render configuration for the Level 0 Glance view:
//   - meta-layers (top-level, collapsible)
//   - sub-columns within each meta-layer (finer left-to-right ordering)
//   - a classifier mapping every node to its sub-column
//
// Two orthogonal visual channels:
//   color = criticality tier   (owned by Chokepoint/Summary node components)
//   shape = node type          (owned by ChokepointNode via type-* CSS class)

import type { Node } from "../types";

export type MetaLayerId = "sources" | "materials" | "chips" | "power" | "data_centers";

export const META_LAYERS: { id: MetaLayerId; label: string }[] = [
  { id: "sources",      label: "Supply Sources" },
  { id: "materials",    label: "Materials" },
  { id: "chips",        label: "Chips" },
  { id: "power",        label: "Power" },
  { id: "data_centers", label: "Data Centers" },
];

export interface SubColumn {
  id: string;
  metaLayer: MetaLayerId;
  label: string;
  matches: (n: Node) => boolean;
}

// Order matters — nodes take the first match. Ordering is left-to-right
// within the meta-layer following the paper's supply flow.
export const SUB_COLUMNS: SubColumn[] = [
  // --- Sources ---
  {
    id: "src_countries",
    metaLayer: "sources",
    label: "Countries",
    matches: (n) => n.type === "country_region",
  },

  // --- Materials ---
  // Products are classified into the meta-layer of their DOMINANT CONSUMER
  // (not their paper section). NdFeB magnets go to Data Centers because
  // Vertiv/facilities consume them; HBM/CoWoS/RF go to Chips. Consistent
  // rule across all product nodes.
  {
    id: "mat_minerals",
    metaLayer: "materials",
    label: "Minerals",
    matches: (n) => n.type === "mineral",
  },
  {
    id: "mat_producers",
    metaLayer: "materials",
    label: "Producers",
    matches: (n) =>
      (n.type === "company" && n.sub_category === "rare_earth_producer") ||
      (n.type === "facility" &&
        (n.sub_category === "mine" || n.sub_category === "refinery_separation")),
  },

  // --- Chips ---
  {
    id: "chip_equipment",
    metaLayer: "chips",
    label: "Equipment",
    matches: (n) => n.type === "company" && n.sub_category === "semi_equipment",
  },
  {
    id: "chip_fabs",
    metaLayer: "chips",
    label: "Fabs & Memory",
    matches: (n) =>
      n.type === "company" &&
      (n.sub_category === "foundry" ||
        n.sub_category === "idm_foundry" ||
        n.sub_category === "memory_hbm" ||
        n.sub_category === "diversified_semi"),
  },
  {
    id: "chip_products",
    metaLayer: "chips",
    label: "Semi Products",
    matches: (n) => n.type === "product" && n.layer === "chips",
  },
  {
    id: "chip_designers",
    metaLayer: "chips",
    label: "Designers",
    matches: (n) => n.type === "company" && n.sub_category === "chip_designer_fabless",
  },

  // --- Power ---
  {
    id: "pow_grid",
    metaLayer: "power",
    label: "Grid Equipment",
    matches: (n) => n.type === "company" && n.sub_category === "grid_equipment",
  },
  {
    id: "pow_utilities",
    metaLayer: "power",
    label: "Utilities",
    matches: (n) =>
      n.type === "company" &&
      (n.sub_category === "merchant_power" || n.sub_category === "regulated_utility"),
  },
  {
    id: "pow_plants",
    metaLayer: "power",
    label: "Power Plants",
    matches: (n) => n.type === "facility" && n.sub_category === "power_plant",
  },

  // --- Data Centers ---
  {
    id: "dc_products",
    metaLayer: "data_centers",
    label: "Materials Products",
    matches: (n) => n.type === "product" && n.sub_category === "magnet_product",
  },
  {
    id: "dc_cooling",
    metaLayer: "data_centers",
    label: "Cooling",
    matches: (n) => n.type === "company" && n.sub_category === "cooling",
  },
  {
    id: "dc_operators",
    metaLayer: "data_centers",
    label: "Operators",
    matches: (n) =>
      n.type === "company" &&
      (n.sub_category === "hyperscaler" || n.sub_category === "ai_lab"),
  },
  {
    id: "dc_facilities",
    metaLayer: "data_centers",
    label: "Facilities",
    matches: (n) => n.type === "facility" && n.sub_category === "data_center",
  },
];

export function classifyNode(n: Node): SubColumn | null {
  for (const sc of SUB_COLUMNS) {
    if (sc.matches(n)) return sc;
  }
  return null;
}

export function metaLayerOf(n: Node): MetaLayerId | null {
  return classifyNode(n)?.metaLayer ?? null;
}
