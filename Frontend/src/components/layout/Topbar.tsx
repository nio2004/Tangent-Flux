import { Archive, Columns3, Plus, Search, Settings, Share2 } from "lucide-react";
import { Button } from "../ui/button.tsx";
import { GlobeSignal } from "../dashboard/GlobeSignal.tsx";

interface TopbarProps {
  query: string;
  onQueryChange: (query: string) => void;
  onQuickAdd: () => void;
  activeView: "board" | "graph";
  onViewChange: (view: "board" | "graph") => void;
}

const tabs = [
  { label: "Board", icon: Columns3, view: "board" as const },
  { label: "Graph", icon: Share2, view: "graph" as const },
];

export function Topbar({ query, onQueryChange, onQuickAdd, activeView, onViewChange }: TopbarProps) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <a className="brand-lockup" href="#board" aria-label="Tangent-Flux board">
          <GlobeSignal />
          <span>Tangent-Flux</span>
        </a>
        <nav className="feed-tabs" aria-label="Workspace views">
          {tabs.map(({ label, icon: Icon, view }) => (
            <button
              className={activeView === view ? "feed-tab is-active" : "feed-tab"}
              type="button"
              key={label}
              aria-current={activeView === view ? "page" : undefined}
              onClick={() => onViewChange(view)}
            >
              <Icon size={15} aria-hidden="true" />
              <span>{label}</span>
            </button>
          ))}
          <button className="feed-tab" type="button" disabled>
            <Archive size={15} aria-hidden="true" />
            <span>Archive</span>
          </button>
        </nav>
      </div>

      <label className="search-box">
        <Search size={18} aria-hidden="true" />
        <span className="sr-only">Search ideas</span>
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search signals, sources, tags"
        />
      </label>

      <div className="top-actions">
        <Button variant="hot" onClick={onQuickAdd}>
          <Plus size={17} aria-hidden="true" />
          <span>Quick Add</span>
        </Button>
        <Button variant="ghost" size="icon" aria-label="Open workspace settings">
          <Settings size={18} aria-hidden="true" />
        </Button>
      </div>
    </header>
  );
}
