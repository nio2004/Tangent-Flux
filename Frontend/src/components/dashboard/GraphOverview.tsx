import { Maximize2, RefreshCw, Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { OverviewGraph, OverviewGraphEdge, OverviewGraphNode } from "../../types/idea.ts";
import { Badge } from "../ui/badge.tsx";
import { Button } from "../ui/button.tsx";

interface GraphOverviewProps {
  graph: OverviewGraph | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function GraphOverview({ graph, loading, error, onRefresh }: GraphOverviewProps) {
  const [query, setQuery] = useState("");
  const [activeKind, setActiveKind] = useState<"all" | "idea" | "concept">("all");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [fullViewOpen, setFullViewOpen] = useState(false);
  const nodes = graph?.nodes ?? [];
  const edges = graph?.edges ?? [];

  const filteredNodes = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return nodes.filter((node) => {
      const matchesKind = activeKind === "all" || node.kind === activeKind;
      const matchesQuery =
        !normalized ||
        [node.label, node.summary, node.status ?? "", ...(node.tags ?? [])].some((value) =>
          value.toLowerCase().includes(normalized),
        );
      return matchesKind && matchesQuery;
    });
  }, [activeKind, nodes, query]);

  const filteredNodeIds = new Set(filteredNodes.map((node) => node.id));
  const visibleEdges = edges.filter((edge) => filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target));
  const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? filteredNodes[0] ?? null;
  const selectedEdges = selectedNode ? edges.filter((edge) => edge.source === selectedNode.id || edge.target === selectedNode.id) : [];
  const conceptCount = nodes.filter((node) => node.kind === "concept").length;
  const bridgeCount = edges.filter((edge) => edge.edgeType === "BRIDGE").length;

  return (
    <section className="graph-overview" aria-label="Workspace graph visualization">
      <div className="graph-overview-header">
        <div>
          <p className="eyebrow">Graph View</p>
          <h2>LLM + heuristic memory graph</h2>
        </div>
        <div className="graph-actions">
          <Button variant="ghost" onClick={() => setFullViewOpen(true)} disabled={!nodes.length}>
            <Maximize2 size={16} aria-hidden="true" />
            <span>Full view</span>
          </Button>
          <Button variant="ghost" onClick={onRefresh}>
            <RefreshCw size={16} aria-hidden="true" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      <div className="graph-stats" aria-label="Graph statistics">
        <span>{nodes.filter((node) => node.kind === "idea").length} ideas</span>
        <span>{conceptCount} concept nodes</span>
        <span>{edges.length} edges</span>
        <span>{bridgeCount} bridge hints</span>
      </div>

      <div className="graph-toolbar">
        <label className="graph-search">
          <Search size={16} aria-hidden="true" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search graph memory" />
        </label>
        <div className="graph-kind-toggle" aria-label="Graph node filter">
          {(["all", "idea", "concept"] as const).map((kind) => (
            <button key={kind} type="button" className={activeKind === kind ? "is-active" : ""} onClick={() => setActiveKind(kind)}>
              {kind}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="graph-status">Loading graph...</p>}
      {error && <p className="graph-status">{error}</p>}

      <div className="graph-explorer-layout">
        <GraphCanvas nodes={filteredNodes} edges={visibleEdges} selectedNodeId={selectedNode?.id} onSelectNode={setSelectedNodeId} loading={loading} />
        <GraphInspector node={selectedNode} edges={selectedEdges} nodes={nodes} />
      </div>

      <div className="graph-edge-list">
        <h3>Relationships</h3>
        {visibleEdges.length === 0 && <p>No visible edges yet.</p>}
        {visibleEdges.slice(0, 24).map((edge) => (
          <GraphEdgeRow edge={edge} nodes={nodes} key={edge.id} />
        ))}
      </div>

      {fullViewOpen && (
        <div className="graph-fullscreen" role="dialog" aria-modal="true" aria-label="Full memory graph">
          <div className="graph-fullscreen-shell">
            <div className="graph-overview-header">
              <div>
                <p className="eyebrow">Full Graph</p>
                <h2>Explore memory structure</h2>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setFullViewOpen(false)} aria-label="Close full graph">
                <X size={18} aria-hidden="true" />
              </Button>
            </div>
            <GraphCanvas
              nodes={filteredNodes}
              edges={visibleEdges}
              selectedNodeId={selectedNode?.id}
              onSelectNode={setSelectedNodeId}
              loading={loading}
              full
            />
            <GraphInspector node={selectedNode} edges={selectedEdges} nodes={nodes} />
          </div>
        </div>
      )}
    </section>
  );
}

function GraphCanvas({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
  loading,
  full = false,
}: {
  nodes: OverviewGraphNode[];
  edges: OverviewGraphEdge[];
  selectedNodeId?: string | null;
  onSelectNode: (id: string) => void;
  loading: boolean;
  full?: boolean;
}) {
  return (
    <div className={full ? "graph-canvas graph-canvas-full" : "graph-canvas"}>
      {nodes.length === 0 && !loading && (
        <p className="graph-status">No graph memory yet. Initialize an idea to create concept nodes.</p>
      )}
      {edges.map((edge) => (
        <GraphEdgeLine key={edge.id} edge={edge} nodes={nodes} />
      ))}
      {nodes.map((node, index) => (
        <GraphNodeCard
          key={node.id}
          node={node}
          index={index}
          total={nodes.length}
          selected={node.id === selectedNodeId}
          onSelect={() => onSelectNode(node.id)}
        />
      ))}
    </div>
  );
}

function GraphNodeCard({
  node,
  index,
  total,
  selected,
  onSelect,
}: {
  node: OverviewGraphNode;
  index: number;
  total: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const { x, y } = getGraphNodePosition(node, index, total);
  return (
    <button
      type="button"
      className={[
        "graph-node-card",
        node.kind === "idea" ? "is-idea" : "",
        selected ? "is-selected" : "",
      ].filter(Boolean).join(" ")}
      style={{ left: `${x}%`, top: `${y}%` }}
      onClick={onSelect}
    >
      <strong>{node.label}</strong>
      <small>{node.kind === "idea" ? node.status : `${node.memberCount ?? 0} chunks`}</small>
    </button>
  );
}

function GraphInspector({ node, edges, nodes }: { node: OverviewGraphNode | null; edges: OverviewGraphEdge[]; nodes: OverviewGraphNode[] }) {
  if (!node) {
    return (
      <aside className="graph-inspector">
        <p className="eyebrow">Inspector</p>
        <h3>Select a node</h3>
        <p>Click an idea or concept node to inspect its LLM summary, heuristic memberships, and connected edges.</p>
      </aside>
    );
  }

  return (
    <aside className="graph-inspector">
      <p className="eyebrow">{node.kind === "idea" ? "Idea root" : "Concept cluster"}</p>
      <h3>{node.label}</h3>
      <p>{node.summary || "No summary yet."}</p>
      <div className="graph-inspector-meta">
        {node.status && <Badge tone="accent">{node.status}</Badge>}
        {node.memberCount !== undefined && <Badge tone="muted">{node.memberCount} chunks</Badge>}
        {node.tags?.slice(0, 4).map((tag) => <Badge tone="muted" key={tag}>{tag}</Badge>)}
      </div>
      <h4>Connected relationships</h4>
      <div className="graph-inspector-edges">
        {edges.length === 0 && <span>No direct edges.</span>}
        {edges.slice(0, 8).map((edge) => {
          const otherId = edge.source === node.id ? edge.target : edge.source;
          const other = nodes.find((item) => item.id === otherId);
          return (
            <article key={edge.id}>
              <strong>{other?.label ?? otherId}</strong>
              <small>{edge.edgeType} · {edge.weight.toFixed(2)}</small>
            </article>
          );
        })}
      </div>
    </aside>
  );
}

function GraphEdgeRow({ edge, nodes }: { edge: OverviewGraphEdge; nodes: OverviewGraphNode[] }) {
  const source = nodes.find((node) => node.id === edge.source)?.label ?? edge.source;
  const target = nodes.find((node) => node.id === edge.target)?.label ?? edge.target;
  return (
    <article>
      <Badge tone={edge.edgeType === "BRIDGE" ? "accent" : "muted"}>{edge.edgeType}</Badge>
      <span>{source} -&gt; {target}</span>
      <small>{edge.reason} · weight {edge.weight.toFixed(2)}</small>
    </article>
  );
}

function GraphEdgeLine({ edge, nodes }: { edge: OverviewGraphEdge; nodes: OverviewGraphNode[] }) {
  const sourceIndex = nodes.findIndex((node) => node.id === edge.source);
  const targetIndex = nodes.findIndex((node) => node.id === edge.target);
  if (sourceIndex < 0 || targetIndex < 0) {
    return null;
  }

  const source = getGraphNodePosition(nodes[sourceIndex], sourceIndex, nodes.length);
  const target = getGraphNodePosition(nodes[targetIndex], targetIndex, nodes.length);
  const dx = target.x - source.x;
  const dy = target.y - source.y;

  return (
    <span
      className={edge.edgeType === "BRIDGE" ? "graph-edge-line is-bridge" : "graph-edge-line"}
      title={`${edge.edgeType} ${edge.weight.toFixed(2)}: ${edge.reason}`}
      style={{
        left: `${source.x}%`,
        top: `${source.y}%`,
        width: `${Math.hypot(dx, dy)}%`,
        opacity: Math.max(0.35, Math.min(1, edge.weight)),
        transform: `rotate(${Math.atan2(dy, dx) * (180 / Math.PI)}deg)`,
      }}
    />
  );
}

function getGraphNodePosition(node: OverviewGraphNode, index: number, total: number) {
  const ideaCountBias = node.kind === "idea" ? 0 : Math.PI / Math.max(total, 1);
  const angle = (index / Math.max(total, 1)) * Math.PI * 2 + ideaCountBias;
  const radius = node.kind === "idea" ? 26 : 40;
  const x = 50 + Math.cos(angle) * radius;
  const y = 50 + Math.sin(angle) * radius;
  return { x: Math.max(6, Math.min(88, x)), y: Math.max(8, Math.min(86, y)) };
}
