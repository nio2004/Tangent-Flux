import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import type { MouseEvent } from "react";
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
    setResourceIndex((current) => (current + direction + resources.length) % resources.length);
  }

  function showNextResource() {
    setResourceIndex((current) => (current + 1) % resources.length);
  }

  function openResource(event: MouseEvent<HTMLButtonElement>, resource: ResourcePreview) {
    event.stopPropagation();
    if (!resource.sourceUrl) {
      return;
    }
    window.open(resource.sourceUrl, "_blank", "noopener,noreferrer");
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
        <AnimatePresence mode="popLayout">
          {resources.map((resource, index) => {
            const offset = (index - resourceIndex + resources.length) % resources.length;
            const active = offset === 0;

            return (
              <motion.article
                className={`resource-slide offset-${offset}`}
                key={resource.title}
                role="button"
                tabIndex={0}
                onClick={showNextResource}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    showNextResource();
                  }
                }}
                initial={{ opacity: 0, y: 24, rotate: -1 }}
                animate={{
                  opacity: active ? 1 : offset === 1 ? 0.62 : 0.22,
                  x: offset * 18,
                  y: offset * 18,
                  scale: 1 - offset * 0.055,
                  rotate: offset * 1.4,
                  zIndex: resources.length - offset,
                }}
                transition={{ type: "spring", stiffness: 260, damping: 30 }}
                aria-label={active ? `Open next resource after ${resource.title}` : `Show ${resource.title}`}
              >
                <div className="resource-feature-top">
                  <Badge tone="accent">{resource.type}</Badge>
                  <span>
                    {String(index + 1).padStart(2, "0")} / {String(resources.length).padStart(2, "0")}
                  </span>
                </div>
                <h4>{resource.title}</h4>
                <p>{resource.description}</p>
                <div className="resource-meta">
                  <span>{resource.meta}</span>
                  <button
                    className="resource-open"
                    type="button"
                    onClick={(event) => openResource(event, resource)}
                    disabled={!resource.sourceUrl}
                    aria-label={resource.sourceUrl ? `Open ${resource.title}` : `No source URL for ${resource.title}`}
                    title={resource.sourceUrl ? `Open ${resource.title}` : "No source URL available"}
                  >
                    <ExternalLink size={14} aria-hidden="true" />
                  </button>
                </div>
              </motion.article>
            );
          })}
        </AnimatePresence>
      </div>
      <div className="resource-dots" aria-label="Resource position">
        {resources.map((resource, index) => (
          <button
            key={resource.title}
            className={resourceIndex === index ? "is-active" : ""}
            type="button"
            onClick={() => setResourceIndex(index)}
            aria-label={`Show resource ${index + 1}`}
          />
        ))}
      </div>
    </section>
  );
}
