import { useContext, useEffect, useMemo, useRef, useState } from "react";

import type { Glance, Node } from "../../types";
import { displayTier } from "../../types";
import { HoverContext } from "../../lib/hover-context";
import type { BadgeDecisions } from "../../lib/badge-decisions";
import { api } from "../../api";

// Pass I / I.1 — trail narration strip.
//
// Reads hoveredId / pinnedId from HoverContext (same activeTrailId rule
// as the diagram: hover previews the pin). Fetches narration.glance
// lazily with a 150 ms debounce and caches responses in an in-memory
// Map keyed by node id (bounded by graph size).
//
// CRITICAL: TrailStrip must NEVER cause GlanceView's flowNodes /
// flowEdges memos to rebuild. It reads state from the same
// HoverContext the diagram nodes already read; it does not sit in the
// memo dependency chain.
//
// AC5 — no English composed here. All wording (including section
// labels "Supplies" / "Reach" / "Heaviest paths", chip labels, and
// every supply-line string) is authored in narration.yaml and comes
// through /nodes/{id}/narration. This file interpolates DATA
// (counts, shares) — it does not compose sentences.
//
// AC4 — chips read glance.stats, NOT the client-side computeReachable
// walk. The client walk runs over RENDERED edges, which shrink when
// meta-layers collapse into summary nodes, so client counts drift
// with view state. One canonical source.

const DEBOUNCE_MS = 150;
const TYPE_GLYPH: Record<string, string> = {
  mineral: "⛏",
  product: "◆",
  company: "▭",
  facility: "🏭",
  country_region: "🌐",
};

interface Props {
  nodes: Node[];
  badges: BadgeDecisions;
}

export function TrailStrip({ nodes, badges }: Props) {
  const ctx = useContext(HoverContext);
  const activeId = ctx.hoveredId ?? ctx.pinnedId;
  const nodeById = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  const cacheRef = useRef<Map<string, Glance | null>>(new Map());
  const [glance, setGlance] = useState<Glance | null>(null);
  const [pending, setPending] = useState<boolean>(false);

  useEffect(() => {
    if (!activeId) {
      setGlance(null);
      setPending(false);
      return;
    }
    const cached = cacheRef.current.get(activeId);
    if (cached !== undefined) {
      setGlance(cached);
      setPending(false);
      return;
    }
    setPending(true);
    let cancelled = false;
    const timer = setTimeout(() => {
      api
        .narration(activeId)
        .then((n) => {
          if (cancelled) return;
          const g = n.glance ?? null;
          cacheRef.current.set(activeId, g);
          setGlance(g);
          setPending(false);
        })
        .catch(() => {
          if (cancelled) return;
          cacheRef.current.set(activeId, null);
          setGlance(null);
          setPending(false);
        });
    }, DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [activeId]);

  if (!activeId) {
    return (
      <div className="trail-strip trail-strip--empty">
        <span className="trail-strip-hint">
          hover or pin a node to see its role, supply edges, downstream reach, and heaviest paths
        </span>
      </div>
    );
  }

  const node = nodeById.get(activeId);
  if (!node) return null;

  const tier = displayTier(node);
  const badge = badges.badgeByHost.get(node.id);
  const glyph = TYPE_GLYPH[node.type] ?? "•";
  const pinnedTag = ctx.pinnedId === node.id && ctx.hoveredId === null;

  const stats = glance?.stats;
  const labels = glance?.labels;
  const sectionLabels = labels?.sections ?? {};
  const chipLabels = labels?.chips ?? {};

  return (
    <div className="trail-strip">
      <div className="trail-strip-identity">
        <span className="trail-strip-glyph" aria-hidden>{glyph}</span>
        <span className="trail-strip-name">{node.name}</span>
        <span className={`trail-strip-chip tier-chip tier-${tier}`}>{tier}</span>
        {badge && (
          <span className="trail-strip-chip trail-strip-badge" title={badge.name}>
            {badge.flag} {badge.name}
          </span>
        )}
        {pinnedTag && (
          <span className="trail-strip-chip trail-strip-pinned">pinned</span>
        )}
      </div>

      {stats && chipLabels && (
        <div className="trail-strip-stat-chips" aria-label="reach statistics">
          <StatChip label={chipLabels.trail_label} value={stats.downstream_nodes} />
          <StatChip
            label={chipLabels.critical_label}
            value={stats.critical_reached.length}
            emphasis={stats.critical_reached.length > 0 ? "critical" : undefined}
          />
          <StatChip
            label={chipLabels.high_label}
            value={stats.high_reached.length}
            emphasis={stats.high_reached.length > 0 ? "high" : undefined}
          />
          <StatChip label={chipLabels.layers_label} value={stats.layers_crossed} />
        </div>
      )}

      <div className="trail-strip-body">
        <div className="trail-strip-summary">
          {glance?.summary ??
            (pending ? <span className="trail-strip-pending">loading…</span> : null)}
        </div>

        {glance && glance.supply_lines.length > 0 && (
          <Section label={sectionLabels.supply_lines}>
            <div className="trail-strip-supply-lines">
              {glance.supply_lines.map((line, i) => (
                <span
                  key={`${i}-${line.target_id ?? "overflow"}`}
                  className={
                    line.kind === "overflow"
                      ? "trail-strip-supply-line trail-strip-supply-line--overflow"
                      : "trail-strip-supply-line"
                  }
                >
                  {line.text}
                </span>
              ))}
            </div>
          </Section>
        )}

        {glance?.reach && (
          <Section label={sectionLabels.reach}>
            <div className="trail-strip-reach">{glance.reach}</div>
          </Section>
        )}

        {glance && glance.paths.length > 0 && (
          <Section label={sectionLabels.paths}>
            <div className="trail-strip-paths">
              {glance.paths.map((path, pi) => (
                <div key={pi} className="trail-strip-path">
                  {path.map((step, si) => (
                    <span key={si} className="trail-strip-step">
                      {si === 0 && (
                        <span className="trail-strip-step-node">{step.from}</span>
                      )}
                      <span className="trail-strip-step-verb">
                        {" — "}{step.verb}{" "}
                        <span className="trail-strip-step-share">
                          {(step.share * 100).toFixed(0)}%
                        </span>
                        {" → "}
                      </span>
                      <span className="trail-strip-step-node">{step.to}</span>
                    </span>
                  ))}
                </div>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

function Section({
  label,
  children,
}: {
  label?: string;
  children: React.ReactNode;
}) {
  if (!label) return <>{children}</>;
  return (
    <div className="trail-strip-section">
      <div className="trail-strip-section-label">{label}</div>
      {children}
    </div>
  );
}

function StatChip({
  label,
  value,
  emphasis,
}: {
  label?: string;
  value: number;
  emphasis?: "critical" | "high";
}) {
  if (!label) return null;
  const cls = emphasis
    ? `trail-strip-stat trail-strip-stat--${emphasis}`
    : "trail-strip-stat";
  return (
    <span className={cls}>
      <span className="trail-strip-stat-value">{value}</span>
      <span className="trail-strip-stat-label">{label}</span>
    </span>
  );
}
