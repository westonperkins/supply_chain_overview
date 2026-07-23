import { Handle, Position } from "@xyflow/react";
import type { Node } from "../../types";
import { useHoverState } from "../../lib/hover-context";

type Data = {
  node: Node;
  badge?: { flag: string; name: string };
};

export function ChokepointNode({ id, data }: { id: string; data: Data }) {
  const n = data.node;
  const badge = data.badge;
  // Pass F — read baseline_tier (structural). current_tier waits for the
  // news-ingestion pass. Default to "unscored" when the field is absent so
  // an unfamiliar node reads as "not rated" rather than silently green.
  const tier = n.dynamic.baseline_tier ?? "unscored";
  const icon =
    n.type === "facility" ? "🏭"
    : n.type === "mineral"  ? "⛏"
    : n.type === "product"  ? "◆"
    : null;

  const { focused, inTrail, dimmed } = useHoverState(id);
  // Inline styles because CSS class specificity was fighting with the base
  // .tier-critical rules and losing. Inline styles beat class selectors.
  const hoverStyle: React.CSSProperties = focused
    ? {
        outline: "3px solid var(--accent)",
        outlineOffset: "3px",
        transform: "scale(1.04)",
        zIndex: 30,
        transition: "outline 0.12s ease, transform 0.12s ease",
      }
    : inTrail
    ? {
        outline: "2px solid var(--accent)",
        outlineOffset: "2px",
        zIndex: 20,
        transition: "outline 0.12s ease",
      }
    : dimmed
    ? { opacity: 0.12, transition: "opacity 0.15s ease" }
    : { transition: "outline 0.12s ease, opacity 0.15s ease, transform 0.12s ease" };

  return (
    <div className={`glance-node type-${n.type} tier-${tier}`} style={hoverStyle}>
      <Handle type="target" position={Position.Left} />
      <div className="glance-node-body">
        <div className="glance-node-title">
          {icon && <span className="glance-node-icon">{icon}</span>}
          <span className="glance-node-name">{n.name}</span>
        </div>
        <div className="glance-node-meta">
          <span className="glance-node-cat">{n.sub_category ?? n.type}</span>
          <span className={`glance-tier tier-${tier}`}>{tier}</span>
        </div>
        {badge && (
          <div className="glance-node-badge" title={`located in ${badge.name}`}>
            <span className="glance-node-badge-flag">{badge.flag}</span>
            <span className="glance-node-badge-name">{badge.name}</span>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
