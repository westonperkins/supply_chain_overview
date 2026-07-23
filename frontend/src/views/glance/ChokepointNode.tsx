import { Handle, Position } from "@xyflow/react";
import type { Node } from "../../types";
import { displayTier } from "../../types";
import { useHoverState } from "../../lib/hover-context";

type Data = {
  node: Node;
  badge?: { flag: string; name: string };
};

export function ChokepointNode({ id, data }: { id: string; data: Data }) {
  const n = data.node;
  const badge = data.badge;
  // Pass G — displayTier applies the belt-and-braces guard:
  // baseline_severity === null → "unscored" regardless of any other
  // tier field. Pass H's cascade can raise current_severity on unscored
  // nodes and re-derive a scored current_tier from it; without this
  // guard, a future colouring-by-current mode could paint them green.
  const tier = displayTier(n);
  const icon =
    n.type === "facility" ? "🏭"
    : n.type === "mineral"  ? "⛏"
    : n.type === "product"  ? "◆"
    : null;

  const { focused, inTrail, dimmed, pinned } = useHoverState(id);
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
    <div className={`glance-node type-${n.type} tier-${tier}${pinned ? " is-pinned" : ""}`} style={hoverStyle}>
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
