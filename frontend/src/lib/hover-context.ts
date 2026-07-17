import { createContext, useContext } from "react";

// Hover state is delivered to custom node components via React context so the
// node/edge ARRAYS passed to React Flow stay identity-stable across hover
// events. Previous approach (rebuilding arrays on hover) caused React Flow to
// see new object references and re-mount everything — visible as flashing +
// occasional total vanish.
export interface HoverState {
  hoveredId: string | null;
  trailNodes: Set<string> | null;   // nodes in the hovered node's up+down chain (incl. the hovered node)
  trailEdges: Set<string> | null;   // edges in that chain
}

export const HoverContext = createContext<HoverState>({
  hoveredId: null,
  trailNodes: null,
  trailEdges: null,
});

export function useHoverState(id: string) {
  const ctx = useContext(HoverContext);
  if (ctx.trailNodes === null) {
    return { focused: false, inTrail: false, dimmed: false };
  }
  const focused = ctx.hoveredId === id;
  const inTrail = ctx.trailNodes.has(id);
  const dimmed = !inTrail;
  return { focused, inTrail, dimmed };
}
