import { Handle, Position } from "@xyflow/react";
import type { MetaLayerId } from "../../lib/render-config";
import { useHoverState } from "../../lib/hover-context";

interface SummaryData {
  metaLayerId: MetaLayerId;
  label: string;
  worstTier: "critical" | "high" | "moderate" | "none";
  tierCounts: {
    critical: number;
    high: number;
    moderate: number;
    none: number;
    unscored: number;  // Pass F — first-class visual state, not a hidden fallback
  };
  count: number;
}

export function SummaryNode({ id, data }: { id: string; data: SummaryData }) {
  const { label, worstTier, tierCounts, count } = data;
  const { focused, inTrail, dimmed } = useHoverState(id);
  const hoverStyle: React.CSSProperties = focused
    ? { outline: "3px solid var(--accent)", outlineOffset: "3px", transform: "scale(1.04)", zIndex: 30 }
    : inTrail
    ? { outline: "2px solid var(--accent)", outlineOffset: "2px", zIndex: 20 }
    : dimmed
    ? { opacity: 0.12 }
    : {};
  return (
    <div className={`glance-summary tier-${worstTier}`} style={hoverStyle}>
      <Handle type="target" position={Position.Left} />
      <div className="glance-summary-title">{label}</div>
      <div className="glance-summary-count">{count} nodes · collapsed</div>
      <div className="glance-summary-histogram">
        {tierCounts.critical > 0 && (
          <span className="glance-summary-bucket critical" title={`${tierCounts.critical} critical`}>
            {tierCounts.critical}
          </span>
        )}
        {tierCounts.high > 0 && (
          <span className="glance-summary-bucket high" title={`${tierCounts.high} high`}>
            {tierCounts.high}
          </span>
        )}
        {tierCounts.moderate > 0 && (
          <span className="glance-summary-bucket moderate" title={`${tierCounts.moderate} moderate`}>
            {tierCounts.moderate}
          </span>
        )}
        {tierCounts.none > 0 && (
          <span className="glance-summary-bucket none" title={`${tierCounts.none} none`}>
            {tierCounts.none}
          </span>
        )}
        {tierCounts.unscored > 0 && (
          <span className="glance-summary-bucket unscored" title={`${tierCounts.unscored} unscored`}>
            {tierCounts.unscored}
          </span>
        )}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
