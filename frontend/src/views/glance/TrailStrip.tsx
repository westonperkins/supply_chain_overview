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
// Pass I.1 correction — a failed fetch is NOT cached for the session.
// Next hover retries the request. To avoid hammering a dead backend
// (e.g. a long restart), the failure gets a short-TTL marker instead
// — 10 s is enough to ride through a restart while still self-healing
// without a hard reload.
const FAILURE_TTL_MS = 10_000;
const TYPE_GLYPH: Record<string, string> = {
  mineral: "⛏",
  product: "◆",
  company: "▭",
  facility: "🏭",
  country_region: "🌐",
};

// Pass I.1 correction — the ONE authored string that must not come from
// narration.yaml. Rendering it depends precisely on the fetch that just
// failed, so serving it via that same fetch would be a lamp that needs
// electricity to report a power cut. Hardcoded in TS as UI chrome —
// same category as the empty-state hint that already lives here, not
// data prose. Every glance-DATA sentence continues to be authored on
// the backend.
const ERROR_HINT = "narration unavailable — hover again to retry";

interface Props {
  nodes: Node[];
  badges: BadgeDecisions;
}

export function TrailStrip({ nodes, badges }: Props) {
  const ctx = useContext(HoverContext);
  const activeId = ctx.hoveredId ?? ctx.pinnedId;
  const nodeById = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  // Success cache — Glance objects live for the session.
  const cacheRef = useRef<Map<string, Glance>>(new Map());
  // Failure cache — timestamp of last failed fetch per id. Cleared on
  // success or when TTL expires; never session-sticky. This is the
  // fix for the blank-strip bug (a single transient failure permanently
  // blanking that node until hard reload, with no console output).
  const failureRef = useRef<Map<string, number>>(new Map());
  const [glance, setGlance] = useState<Glance | null>(null);
  const [pending, setPending] = useState<boolean>(false);
  const [failed, setFailed] = useState<boolean>(false);

  useEffect(() => {
    if (!activeId) {
      setGlance(null);
      setPending(false);
      setFailed(false);
      return;
    }
    const cached = cacheRef.current.get(activeId);
    if (cached !== undefined) {
      setGlance(cached);
      setPending(false);
      setFailed(false);
      return;
    }
    // If a recent failure is still in-window, show the failure state
    // without hitting the backend again. Beyond the TTL, retry on
    // this render.
    const lastFailure = failureRef.current.get(activeId);
    if (lastFailure !== undefined && Date.now() - lastFailure < FAILURE_TTL_MS) {
      setGlance(null);
      setPending(false);
      setFailed(true);
      return;
    }
    setPending(true);
    setFailed(false);
    let cancelled = false;
    const timer = setTimeout(() => {
      api
        .narration(activeId)
        .then((n) => {
          if (cancelled) return;
          const g = n.glance ?? null;
          if (g) {
            cacheRef.current.set(activeId, g);
            failureRef.current.delete(activeId);
          }
          setGlance(g);
          setPending(false);
          setFailed(false);
        })
        .catch((err) => {
          if (cancelled) return;
          // Pass I.1 correction — do NOT write to the success cache.
          // Record a timestamp so a subsequent hover in the next 10 s
          // shows the failure state without hammering the backend,
          // but never lock the id out for the session. And surface the
          // error to the console; the swallowed error is what turned
          // this into a screenshot-diagnosis last time.
          console.error("glance fetch failed", activeId, err);
          failureRef.current.set(activeId, Date.now());
          setGlance(null);
          setPending(false);
          setFailed(true);
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
            (pending ? (
              <span className="trail-strip-pending">loading…</span>
            ) : failed ? (
              <span className="trail-strip-error">{ERROR_HINT}</span>
            ) : null)}
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
