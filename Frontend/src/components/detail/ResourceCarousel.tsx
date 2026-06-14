import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { useState } from "react";
import type { ResourcePreview } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";
import { Badge } from "../ui/badge.tsx";

interface ResourceCarouselProps {
  resources: ResourcePreview[];
}

export function ResourceCarousel({ resources }: ResourceCarouselProps) {
  const [resourceIndex, setResourceIndex] = useState(0);

  function move(direction: number) {
    if (!resources.length) {
      return;
    }
    setResourceIndex((current) => (current + direction + resources.length) % resources.length);
  }

  return (
    <section className="workspace-panel resource-carousel" id="resources">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Resource Stack</p>
          <h3>Linked evidence</h3>
        </div>
        <div className="resource-controls">
          <Button variant="ghost" size="icon" onClick={() => move(-1)} aria-label="Previous resource">
            <ChevronLeft size={18} aria-hidden="true" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => move(1)} aria-label="Next resource">
            <ChevronRight size={18} aria-hidden="true" />
          </Button>
        </div>
      </div>

      <div className="resource-carousel-stage" aria-live="polite">
        {resources.length === 0 && (
          <article className="resource-slide offset-0">
            <div className="resource-slide-top">
              <Badge tone="muted">Empty</Badge>
              <span>0 / 0</span>
            </div>
            <h4>No resources yet</h4>
            <p>Attach a link or paste a source from Studio Controls.</p>
            <small>Waiting for evidence</small>
          </article>
        )}
        {resources.map((resource, index) => {
          const offset = (index - resourceIndex + resources.length) % resources.length;
          return (
            <article className={`resource-slide offset-${offset}`} key={resource.title}>
              <div className="resource-slide-top">
                <Badge tone="accent">{resource.type}</Badge>
                <span>{index + 1} / {resources.length}</span>
              </div>
              <h4>{resource.title}</h4>
              <p>{resource.description}</p>
              <small>
                {resource.meta}
                <ExternalLink size={14} aria-hidden="true" />
              </small>
            </article>
          );
        })}
      </div>
      {resources.length > 0 && <div className="resource-dots" aria-label="Resource position">
        {resources.map((resource, index) => (
          <button
            key={resource.title}
            className={resourceIndex === index ? "is-active" : ""}
            type="button"
            onClick={() => setResourceIndex(index)}
            aria-label={`Show resource ${index + 1}`}
          />
        ))}
      </div>}
    </section>
  );
}
