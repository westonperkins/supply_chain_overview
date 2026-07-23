import { useEffect, useRef, useState } from "react";

// Pass I Part 4 — "How to read this" popover.
//
// Static explanation of Level 0's visual grammar: five tier swatches,
// node shapes, edge thickness, and what the highlighted trail means.
// A single button in the layer-controls row toggles it. Content is
// static (no data flow), dismissible by outside click or Escape.
//
// Deliberately not authored via narration.yaml — this describes how
// the FRONTEND renders (shapes, thickness, dashed edges), which is
// UI-mechanics, not data prose. narration.yaml continues to be the
// only place that DATA-driven wording lives.

export function HowToRead() {
  const [open, setOpen] = useState<boolean>(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onClick = (e: MouseEvent) => {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as HTMLElement)) setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    // Defer to next tick so the toggle click doesn't immediately re-close.
    const t = setTimeout(() => {
      window.addEventListener("mousedown", onClick);
    }, 0);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onClick);
      clearTimeout(t);
    };
  }, [open]);

  return (
    <div className="how-to-read" ref={rootRef}>
      <button
        className={`layer-toggle how-to-read-toggle ${open ? "is-expanded" : "is-collapsed"}`}
        onClick={() => setOpen((v) => !v)}
        title="Legend + what the highlighted trail means"
      >
        <span className="layer-toggle-icon">?</span>
        <span className="layer-toggle-label">How to read this</span>
      </button>
      {open && (
        <div className="how-to-read-panel" role="dialog" aria-label="How to read Level 0">
          <div className="how-to-read-section">
            <div className="how-to-read-section-title">Colour = chokepoint tier</div>
            <div className="how-to-read-swatch-row">
              <span className="how-to-read-swatch tier-critical">critical</span>
              <span className="how-to-read-swatch tier-high">high</span>
              <span className="how-to-read-swatch tier-moderate">moderate</span>
              <span className="how-to-read-swatch tier-none">none</span>
              <span className="how-to-read-swatch tier-unscored">unscored</span>
            </div>
            <div className="how-to-read-note">
              Unscored = the engine refused to score because a required static axis
              (substitutability or lead-time) is missing. Not a low-severity signal.
            </div>
          </div>

          <div className="how-to-read-section">
            <div className="how-to-read-section-title">Shape = node type</div>
            <div className="how-to-read-swatch-row">
              <span className="how-to-read-shape">⛏ mineral</span>
              <span className="how-to-read-shape">◆ product</span>
              <span className="how-to-read-shape">▭ company</span>
              <span className="how-to-read-shape">🏭 facility</span>
              <span className="how-to-read-shape">🌐 country (supply source)</span>
            </div>
          </div>

          <div className="how-to-read-section">
            <div className="how-to-read-section-title">Edge thickness = weight</div>
            <div className="how-to-read-edges">
              <span className="how-to-read-edge-row">
                <span className="how-to-read-edge how-to-read-edge--strong" /> ≥ 70% share
              </span>
              <span className="how-to-read-edge-row">
                <span className="how-to-read-edge how-to-read-edge--med" /> 30–70% share
              </span>
              <span className="how-to-read-edge-row">
                <span className="how-to-read-edge how-to-read-edge--weak" /> &lt; 30% share
              </span>
              <span className="how-to-read-edge-row">
                <span className="how-to-read-edge how-to-read-edge--dashed" /> operates / located_in (ownership)
              </span>
            </div>
          </div>

          <div className="how-to-read-section">
            <div className="how-to-read-section-title">Highlighted trail</div>
            <div className="how-to-read-note">
              Hovering (or pinning) a node lights up every node and edge that
              reaches it upstream or feeds from it downstream. Everything else
              dims. The strip below reads out the anchor's role and the
              single heaviest path through it — built from real graph edges,
              not the geometry of the highlight.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
