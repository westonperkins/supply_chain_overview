import { Handle, Position } from "@xyflow/react";
import type { Node } from "../../types";
import { COUNTRY_FLAGS } from "../../lib/badge-decisions";
import { useHoverState } from "../../lib/hover-context";

type Data = { node: Node; badge?: { flag: string; name: string } };

const SHORT_NAME: Record<string, string> = {
  "country_region:usa": "USA",
  "country_region:south_korea": "S. Korea",
  "country_region:drc": "DRC",
};

export function CountryNode({ id, data }: { id: string; data: Data }) {
  const n = data.node;
  const flag = COUNTRY_FLAGS[n.id] ?? "🌍";
  const displayName = SHORT_NAME[n.id] ?? n.name;
  const { focused, inTrail, dimmed } = useHoverState(id);
  const hoverStyle: React.CSSProperties = focused
    ? { outline: "3px solid var(--accent)", outlineOffset: "3px", transform: "scale(1.04)", zIndex: 30 }
    : inTrail
    ? { outline: "2px solid var(--accent)", outlineOffset: "2px", zIndex: 20 }
    : dimmed
    ? { opacity: 0.12 }
    : {};
  return (
    <div className="glance-country-node" style={hoverStyle}>
      <Handle type="target" position={Position.Left} />
      <div className="glance-country-flag">{flag}</div>
      <div className="glance-country-name">{displayName}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
