import { useEffect, useState } from "react";
import { api } from "./api";
import type { Edge, Event, Node } from "./types";
import Dashboard from "./views/Dashboard";
import GlanceView from "./views/GlanceView";

type View = "glance" | "detail";

export default function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<View>("glance");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.nodes(), api.edges(), api.events()])
      .then(([n, e, ev]) => {
        setNodes(n);
        setEdges(e);
        setEvents(ev);
        if (n.length > 0) setSelectedId(n[0].id);
      })
      .catch((err) => setError(String(err)));
  }, []);

  if (error) {
    return (
      <div className="error">
        <div>Backend unreachable at http://127.0.0.1:8000</div>
        <div>{error}</div>
        <div style={{ marginTop: 12 }}>Start it with: <code>make backend</code></div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Supply Chain Terminal</h1>
        <div className="app-view-toggle">
          <button
            className={view === "glance" ? "active" : ""}
            onClick={() => setView("glance")}
          >
            Glance
          </button>
          <button
            className={view === "detail" ? "active" : ""}
            onClick={() => setView("detail")}
          >
            Detail
          </button>
        </div>
        <span className="subtitle">
          v0 · domain=ai · {nodes.length} nodes · {events.length} events
        </span>
      </header>
      {view === "glance" ? (
        <GlanceView
          nodes={nodes}
          edges={edges}
          onSelectNode={(id) => {
            setSelectedId(id);
            setView("detail");
          }}
        />
      ) : (
        <Dashboard
          nodes={nodes}
          events={events}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      )}
      <div className="disclaimer">
        Analytical signals only. Not investment advice.
      </div>
    </div>
  );
}
