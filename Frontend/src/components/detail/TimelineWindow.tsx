import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { TimelineEntry } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";

interface TimelineWindowProps {
  entries: TimelineEntry[];
}

export function TimelineWindow({ entries }: TimelineWindowProps) {
<<<<<<< HEAD
  const [start, setStart] = useState(0);
  const visible = entries.slice(start, start + 3);
  const atTop = start === 0;
  const atBottom = entries.length <= 3 || start >= entries.length - 3;
=======
  const windowSize = 5;
  const maxStart = Math.max(0, entries.length - windowSize);
  const [start, setStart] = useState(maxStart);
  const visible = entries.slice(start, start + windowSize);
  const atStart = start === 0;
  const atEnd = start >= maxStart;
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04

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
            disabled={atStart}
            onClick={() => setStart((current) => Math.max(0, current - 1))}
            aria-label="Earlier timeline entries"
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            disabled={atEnd}
            onClick={() => setStart((current) => Math.min(maxStart, current + 1))}
            aria-label="Later timeline entries"
          >
            <ChevronRight size={18} aria-hidden="true" />
          </Button>
        </div>
      </div>
      <div className="timeline">
<<<<<<< HEAD
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
=======
        {visible.map((entry, index) => (
>>>>>>> 6f1c767a5b6ce400673ed3b3987875468dd9fa04
          <article className="thread-item" key={`${entry.time}-${entry.text}`}>
            <span className="thread-dot" aria-hidden="true" />
            <div className="thread-card" tabIndex={0}>
              <span className="thread-label">Log {String(start + index + 1).padStart(2, "0")}</span>
              <time>{entry.time}</time>
              <p>{entry.text}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
