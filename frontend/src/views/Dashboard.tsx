import { useEffect, useState } from "react";
import type { ChokepointTier, Event, Narration, Node, NodeType, SourcedValue } from "../types";
import { displayTier } from "../types";
import { api } from "../api";

interface Props {
  nodes: Node[];
  events: Event[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function Dashboard({ nodes, events, selectedId, onSelect }: Props) {
  const selected = nodes.find((n) => n.id === selectedId) || null;

  return (
    <div className="layout">
      <NodeList nodes={nodes} selectedId={selectedId} onSelect={onSelect} />
      <NodeDetail node={selected} />
      <EventFeed events={events} nodes={nodes} onSelect={onSelect} />
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Node list                                                                    //
// --------------------------------------------------------------------------- //

const TYPE_OPTIONS: NodeType[] = ["mineral", "product", "company", "facility", "country_region"];
// Pass F — `unscored` is a first-class filter chip. `unscored` is NOT
// `none`: the engine refused to score the node (missing static axes),
// as opposed to a scored node that landed low. Ordering keeps scored
// tiers left-to-right by severity, unscored last.
const TIER_OPTIONS: ChokepointTier[] = ["critical", "high", "moderate", "none", "unscored"];

// Empty filter set = "no filter applied (show all)". Non-empty = must be in set.
// Type and Tier filters are ANDed.
function NodeList({
  nodes,
  selectedId,
  onSelect,
}: {
  nodes: Node[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [typeFilter, setTypeFilter] = useState<Set<NodeType>>(new Set());
  const [tierFilter, setTierFilter] = useState<Set<ChokepointTier>>(new Set());

  const toggle = <T,>(setter: React.Dispatch<React.SetStateAction<Set<T>>>, value: T) => {
    setter((prev) => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  };

  const filtered = nodes.filter((n) => {
    if (typeFilter.size > 0 && !typeFilter.has(n.type)) return false;
    // Pass G Part 3 — displayTier guard: baseline_severity === null
    // → "unscored" regardless of any current_tier value.
    const tier = displayTier(n);
    if (tierFilter.size > 0 && !tierFilter.has(tier)) return false;
    return true;
  });

  // Sort by baseline_severity (structural) descending. Unscored nodes
  // have baseline_severity == null → treat as -1 so they land at the
  // bottom (present but not comparable to scored severities).
  const sorted = [...filtered].sort(
    (a, b) =>
      (b.dynamic.baseline_severity ?? -1) - (a.dynamic.baseline_severity ?? -1),
  );

  const filtersActive = typeFilter.size > 0 || tierFilter.size > 0;

  return (
    <div className="pane">
      <h2>Nodes · by severity</h2>

      <div className="filter-block">
        <div className="filter-row">
          <span className="filter-label">Type</span>
          <div className="filter-chips">
            {TYPE_OPTIONS.map((t) => (
              <button
                key={t}
                className={`filter-chip ${typeFilter.has(t) ? "active" : ""}`}
                onClick={() => toggle(setTypeFilter, t)}
              >
                {t.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-row">
          <span className="filter-label">Tier</span>
          <div className="filter-chips">
            {TIER_OPTIONS.map((t) => (
              <button
                key={t}
                className={`filter-chip tier-chip tier-${t} ${tierFilter.has(t) ? "active" : ""}`}
                onClick={() => toggle(setTierFilter, t)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-status">
          <span>{filtered.length} of {nodes.length}</span>
          {filtersActive && (
            <button
              className="filter-clear"
              onClick={() => {
                setTypeFilter(new Set());
                setTierFilter(new Set());
              }}
            >
              clear
            </button>
          )}
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="note">No nodes match the current filters.</div>
      ) : (
        sorted.map((n) => (
          <div
            key={n.id}
            className={`node-row ${n.id === selectedId ? "selected" : ""}`}
            onClick={() => onSelect(n.id)}
          >
            <div>
              <div className="name">{n.name}</div>
              <div className="meta">
                {n.type} · {n.sub_category ?? "—"}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <TierBadge tier={displayTier(n)} />
              <div className="meta" style={{ marginTop: 4 }}>
                {fmt(n.dynamic.baseline_severity)}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function TierBadge({ tier }: { tier: string }) {
  return <span className={`tier ${tier}`}>{tier}</span>;
}

// --------------------------------------------------------------------------- //
// Node detail — the pane that has to make the static/dynamic split visible     //
// --------------------------------------------------------------------------- //

function NodeDetail({ node }: { node: Node | null }) {
  if (!node) {
    return (
      <div className="pane">
        <h2>Detail</h2>
        <div className="note">Select a node.</div>
      </div>
    );
  }

  return (
    <div className="pane">
      <div className="detail-header">
        <h3>{node.name}</h3>
        <div className="id">{node.id}</div>
        {node.description && (
          <p style={{ color: "var(--muted)", marginTop: 8, fontSize: 13 }}>
            {node.description}
          </p>
        )}
      </div>

      {/* Static block */}
      <div className="split-block">
        <div className="label static">
          <span>Static — from the paper</span>
          <span>slow-changing</span>
        </div>
        <div className="kv">
          <div className="k">layer</div>          <div className="v">{node.layer ?? "—"}</div>
          <div className="k">sub_category</div>   <div className="v">{node.sub_category ?? "—"}</div>
          <div className="k">bottleneck</div>     <div className="v">{node.static.bottleneck_type ?? "—"}</div>
          <div className="k">scale</div>          <div className="v">{scaleStr(node.static.scale)}</div>
          <div className="k">substitutability</div><div className="v">{sourced(node.static.substitutability)}</div>
          <div className="k">lead time (yr)</div> <div className="v">{sourced(node.static.lead_time_years)}</div>
          <div className="k">fin. cushion</div>   <div className="v">{sourced(node.static.financial_cushion)}</div>
        </div>
        {node.static.notes && <div className="note">{node.static.notes}</div>}
      </div>

      {/* Dynamic block */}
      <div className="split-block">
        <div className="label dynamic">
          <span>Dynamic — owned by the terminal</span>
          <span>live / derived</span>
        </div>
        <div className="kv">
          <div className="k">baseline tier</div>
          <div className="v">
            <TierBadge tier={node.dynamic.baseline_tier ?? "unscored"} />
            <span className="conf">structural</span>
          </div>
          <div className="k">current tier</div>
          <div className="v">
            <TierBadge tier={node.dynamic.current_tier ?? "unscored"} />
            <span className="conf">event-adjusted</span>
          </div>
          <div className="k">inbound HHI</div>       <div className="v">{fmt(node.dynamic.inbound_hhi)}</div>
          <div className="k">outbound criticality</div><div className="v">{fmt(node.dynamic.outbound_criticality)}</div>
          <div className="k">concentration</div>     <div className="v">{fmt(node.dynamic.concentration)} <span className="conf">max(in,out)</span></div>
          <div className="k">baseline severity</div><div className="v">{fmt(node.dynamic.baseline_severity)} <span className="conf">structural</span></div>
          <div className="k">current severity</div><div className="v">{fmt(node.dynamic.current_severity)} <span className="conf">event-adjusted; == baseline with no active events</span></div>
          {node.dynamic.scored_on_default_axes && node.dynamic.scored_on_default_axes.length > 0 && (
            <>
              <div className="k">missing axes</div>
              <div className="v" style={{ color: "var(--unscored)" }}>
                {node.dynamic.scored_on_default_axes.join(", ")}
              </div>
            </>
          )}
          <div className="k">price</div>           <div className="v">{node.dynamic.price ?? "—"}</div>
          <div className="k">price ex-China</div>  <div className="v">{node.dynamic.price_ex_china ?? "—"}</div>
          <div className="k">market cap</div>      <div className="v">{money(node.dynamic.market_cap)}</div>
        </div>

        {/* Narration — including Pass E "Why this isn't scored" for unscored nodes */}
        <NarrationPanel nodeId={node.id} />

        {node.dynamic.derived_shares && (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 6 }}>
              derived shares (from edges — single source of truth)
            </div>
            {Object.entries(node.dynamic.derived_shares).map(([type, sources]) => (
              <div key={type} style={{ fontSize: 12, fontFamily: "var(--mono)" }}>
                <span style={{ color: "var(--accent)" }}>{type}</span>
                :{" "}
                {Object.entries(sources)
                  .map(([src, w]) => `${src.split(":")[1]} ${(w * 100).toFixed(1)}%`)
                  .join(", ")}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Narration panel — renders /nodes/{id}/narration into the detail card         //
// --------------------------------------------------------------------------- //
// Pass F wired this in so the Pass E "Why this isn't scored" copy is visible
// for the 42 unscored nodes (NVIDIA foremost). For scored nodes it renders the
// existing "why it scores X" prose. The panel gates purely on presence of
// sections in the payload; if the endpoint fails or returns nothing, it
// stays silent rather than fabricating placeholder text.

function NarrationPanel({ nodeId }: { nodeId: string }) {
  const [narr, setNarr] = useState<Narration | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setNarr(null);
    setError(null);
    api
      .narration(nodeId)
      .then((n) => { if (!cancelled) setNarr(n); })
      .catch((e) => { if (!cancelled) setError(String(e)); });
    return () => { cancelled = true; };
  }, [nodeId]);

  if (error) {
    return (
      <div className="note" style={{ marginTop: 12 }}>
        narration unavailable: {error}
      </div>
    );
  }
  if (!narr || narr.sections.length === 0) return null;

  return (
    <div style={{ marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
      <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>
        Narration
      </div>
      {narr.sections.map((s) => (
        <div key={s.key} style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text)", marginBottom: 2 }}>
            {s.title}
          </div>
          <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.5 }}>
            {s.body}
          </div>
        </div>
      ))}
      {narr.caveats.length > 0 && (
        <div style={{ marginTop: 8, fontSize: 11, color: "var(--muted)", fontStyle: "italic" }}>
          {narr.caveats.join(" ")}
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Event feed                                                                   //
// --------------------------------------------------------------------------- //

function EventFeed({
  events,
  nodes,
  onSelect,
}: {
  events: Event[];
  nodes: Node[];
  onSelect: (id: string) => void;
}) {
  const nameOf = (id: string) => nodes.find((n) => n.id === id)?.name ?? id;
  return (
    <div className="pane">
      <h2>Event feed · with cascade</h2>
      {events.map((e) => (
        <div key={e.id} className="event-card">
          <div className="headline">{e.headline}</div>
          <div className="meta">{new Date(e.timestamp).toISOString().slice(0, 10)}</div>
          <div className="severity">severity = {fmt(e.severity)}</div>
          <div className="tags">{e.tags.map((t) => <span key={t}>{t}</span>)}</div>
          <div className="cascade-path">
            <div style={{ fontSize: 10, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>
              propagation path (inspectable)
            </div>
            {e.cascade.map((s, i) => (
              <div
                key={i}
                className="cascade-hop"
                onClick={() => onSelect(s.node_id)}
                style={{ cursor: "pointer" }}
              >
                <span className="hop">hop {s.hop}</span>
                <span className="sev">{fmt(s.severity_at_node)}</span>
                <span>{nameOf(s.node_id)}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// helpers                                                                      //
// --------------------------------------------------------------------------- //

function fmt(x?: number | null): string {
  if (x === undefined || x === null) return "—";
  if (Math.abs(x) < 0.001) return x.toExponential(2);
  return x.toFixed(4);
}

function money(x?: number | null): string {
  if (x === undefined || x === null) return "—";
  if (x >= 1e12) return `$${(x / 1e12).toFixed(2)}T`;
  if (x >= 1e9)  return `$${(x / 1e9).toFixed(2)}B`;
  if (x >= 1e6)  return `$${(x / 1e6).toFixed(2)}M`;
  return `$${x}`;
}

function scaleStr(sv?: SourcedValue<{ value: number; unit: string }> | null): string {
  if (!sv || !sv.value) return "—";
  return `${sv.value.value.toLocaleString()} ${sv.value.unit}`;
}

function sourced(sv?: SourcedValue<number> | null): React.ReactNode {
  if (!sv || sv.value == null) return "—";
  return (
    <>
      {sv.value}
      <span className="conf" title={sv.source_note ?? ""}>{sv.confidence}</span>
    </>
  );
}
