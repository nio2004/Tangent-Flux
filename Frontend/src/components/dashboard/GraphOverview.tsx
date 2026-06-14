import { RefreshCw } from "lucide-react";
import type { OverviewGraph, OverviewGraphNode } from "../../types/idea.ts";
import { Badge } from "../ui/badge.tsx";
import { Button } from "../ui/button.tsx";

interface GraphOverviewProps {
  graph: OverviewGraph | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function GraphOverview({ graph, loading, error, onRefresh }: GraphOverviewProps) {
  const nodes = graph?.nodes ?? [];
  const edges = graph?.edges ?? [];

  return (
    <section className="graph-overview" aria-label="Workspace graph visualization">
      <div className="graph-overview-header">
        <div>
          <p className="eyebrow">Graph View</p>
          <h2>Idea and memory graph</h2>
        </div>
        <Button variant="ghost" onClick={onRefresh}>
          <RefreshCw size={16} aria-hidden="true" />
          <span>Refresh</span>
        </Button>
      </div>

      {loading && <p className="graph-status">Loading graph...</p>}
      {error && <p className="graph-status">{error}</p>}

      <div className="graph-canvas">
        {nodes.length === 0 && !loading && (
          <p className="graph-status">No graph memory yet. Initialize an idea to create concept nodes.</p>
        )}
        {edges.map((edge) => (
          <GraphEdgeLine key={edge.id} edge={edge} nodes={nodes} />
        ))}
        {nodes.map((node, index) => (
          <GraphNodeCard key={node.id} node={node} index={index} total={nodes.length} />
        ))}
      </div>

      <div className="graph-edge-list">
        <h3>Relationships</h3>
        {edges.length === 0 && <p>No edges yet.</p>}
        {edges.slice(0, 24).map((edge) => {
          const source = nodes.find((node) => node.id === edge.source)?.label ?? edge.source;
          const target = nodes.find((node) => node.id === edge.target)?.label ?? edge.target;
          return (
            <article key={edge.id}>
              <Badge tone={edge.edgeType === "BRIDGE" ? "accent" : "muted"}>{edge.edgeType}</Badge>
              <span>
                {source} -&gt; {target}
              </span>
              <small>{edge.reason}</small>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function GraphNodeCard({ node, index, total }: { node: OverviewGraphNode; index: number; total: number }) {
  const { x, y } = getGraphNodePosition(node, index, total);
  return (
    <article
      className={node.kind === "idea" ? "graph-node-card is-idea" : "graph-node-card"}
      style={{ left: `${x}%`, top: `${y}%` }}
    >
      <strong>{node.label}</strong>
      <small>{node.kind === "idea" ? node.status : `${node.memberCount ?? 0} chunks`}</small>
    </article>
  );
}

function GraphEdgeLine({ edge, nodes }: { edge: OverviewGraph["edges"][number]; nodes: OverviewGraphNode[] }) {
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
        transform: `rotate(${Math.atan2(dy, dx) * (180 / Math.PI)}deg)`,
      }}
    />
  );
}

function getGraphNodePosition(node: OverviewGraphNode, index: number, total: number) {
  const angle = (index / Math.max(total, 1)) * Math.PI * 2;
  const radius = node.kind === "idea" ? 34 : 42;
  const x = 50 + Math.cos(angle) * radius;
  const y = 50 + Math.sin(angle) * radius;
  return { x: Math.max(4, Math.min(82, x)), y: Math.max(4, Math.min(82, y)) };
}
