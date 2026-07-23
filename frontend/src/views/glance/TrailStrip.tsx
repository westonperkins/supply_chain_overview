import { useContext, useEffect, useMemo, useRef, useState } from "react";

import type { Glance, Node } from "../../types";
import { displayTier } from "../../types";
import { HoverContext } from "../../lib/hover-context";
import type { BadgeDecisions } from "../../lib/badge-decisions";
import { api } from "../../api";

// Pass I Part 2/3 — trail narration strip.
//
// Reads hoveredId / pinnedId from HoverContext (same activeTrailId rule
// as the diagram itself: hover previews the pin). Fetches the anchor
// node's narration.glance lazily with a 150 ms debounce so brief
// hover-throughs don't fire a request per pixel, and caches responses
// in an in-memory Map keyed by node id (bounded by the graph size ≈ 66).
//
// CRITICAL: TrailStrip must NEVER cause GlanceView's flowNodes /
// flowEdges memos to rebuild. It reads state from the same
// HoverContext the nodes already read; it does not sit in the memo
// dependency chain.
//
// No sentence in this file is composed in TypeScript. All prose comes
// from the /nodes/{id}/narration payload's `glance` field, which is
// assembled in the backend from narration.yaml `glance_summary` and
// `edge_glance_verb`.

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

  // In-memory cache: node id -> Glance (or `null` if the fetch resolved
  // with no glance payload). Kept in a ref so the closure over `cache`
  // doesn't force a re-render, and so re-renders don't blow it away.
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
          hover or pin a node to see its role, top supplier / customer, and heaviest path
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

      <div className="trail-strip-sentence">
        {glance?.sentence ??
          (pending ? <span className="trail-strip-pending">loading…</span> : null)}
      </div>

      {glance?.breadcrumb && glance.breadcrumb.length > 0 && (
        <div className="trail-strip-breadcrumb" aria-label="heaviest path from real edges">
          {glance.breadcrumb.map((step, i) => (
            <span key={i} className="trail-strip-step">
              {i === 0 && (
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
      )}
    </div>
  );
}
