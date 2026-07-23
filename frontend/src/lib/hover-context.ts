import { createContext, useContext } from "react";

// Hover state is delivered to custom node components via React context so the
// node/edge ARRAYS passed to React Flow stay identity-stable across hover
// events. Previous approach (rebuilding arrays on hover) caused React Flow to
// see new object references and re-mount everything — visible as flashing +
// occasional total vanish.
//
// Pass G — `pinnedId` joins hover through the same context. `activeTrailId =
// hoveredId ?? pinnedId` in the provider means hover previews override the
// pinned trail, and moving off reverts to the pin (not to dark). CRITICAL:
// neither hoveredId nor pinnedId may enter the flowNodes / flowEdges memo
// deps — nodes read them through useHoverState, edges through the
// imperative useEffect that classes them.
export interface HoverState {
  hoveredId: string | null;
  pinnedId: string | null;
  trailNodes: Set<string> | null;   // nodes in the (hovered ?? pinned) node's up+down chain
  trailEdges: Set<string> | null;   // edges in that chain
}

export const HoverContext = createContext<HoverState>({
  hoveredId: null,
  pinnedId: null,
  trailNodes: null,
  trailEdges: null,
});

export function useHoverState(id: string) {
  const ctx = useContext(HoverContext);
  // A node is `pinned` iff it's the current pin AND no hover is active
  // (hover takes precedence so previewing shows the hovered node as
  // focused, not the pinned one).
  const pinned = ctx.pinnedId === id && ctx.hoveredId === null;
  if (ctx.trailNodes === null) {
    return { focused: false, inTrail: false, dimmed: false, pinned };
  }
  // "focused" = the source of the trail. Hover wins when present; else pin.
  const activeId = ctx.hoveredId ?? ctx.pinnedId;
  const focused = activeId === id;
  const inTrail = ctx.trailNodes.has(id);
  const dimmed = !inTrail;
  return { focused, inTrail, dimmed, pinned };
}
