import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { TimelineEntry } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";

interface TimelineWindowProps {
  entries: TimelineEntry[];
}

export function TimelineWindow({ entries }: TimelineWindowProps) {
  const [start, setStart] = useState(0);
  const visible = entries.slice(start, start + 3);
  const atTop = start === 0;
  const atBottom = entries.length <= 3 || start >= entries.length - 3;

  return (
    <section className="workspace-panel timeline-window" id="timeline">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Timeline</p>
          <h3>Research journal</h3>
        </div>
        <div className="resource-controls">
          <Button
            variant="ghost"
            size="icon"
            disabled={atTop}
            onClick={() => setStart((current) => Math.max(0, current - 1))}
            aria-label="Earlier timeline entries"
          >
            <ChevronUp size={18} aria-hidden="true" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            disabled={atBottom}
            onClick={() => setStart((current) => Math.min(entries.length - 3, current + 1))}
            aria-label="Later timeline entries"
          >
            <ChevronDown size={18} aria-hidden="true" />
          </Button>
        </div>
      </div>
      <div className="timeline">
        {visible.length === 0 && (
          <article className="thread-item">
            <span className="thread-dot" aria-hidden="true" />
            <div className="thread-card">
              <time>Now</time>
              <p>No timeline entries yet.</p>
            </div>
          </article>
        )}
        {visible.map((entry) => (
          <article className="thread-item" key={`${entry.time}-${entry.text}`}>
            <span className="thread-dot" aria-hidden="true" />
            <div className="thread-card">
              <time>{entry.time}</time>
              <p>{entry.text}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
