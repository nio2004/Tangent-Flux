import { ArrowUpRight, FileText, Layers3 } from "lucide-react";
import type { CSSProperties, MouseEvent } from "react";
import type { Idea } from "../../types/idea.ts";
import { Badge } from "../ui/badge.tsx";

interface IdeaCardProps {
  idea: Idea;
  index: number;
  onOpen: (idea: Idea, rect: DOMRect) => void;
}

const palette = [
  { accent: "#168cff", accent2: "#ffd12f" },
  { accent: "#ff2d3f", accent2: "#168cff" },
  { accent: "#ffd12f", accent2: "#ff2d3f" },
  { accent: "#d8e2ef", accent2: "#168cff" },
];

export function IdeaCard({ idea, index, onOpen }: IdeaCardProps) {
  const colors = palette[index % palette.length];
  const visualHeight = 94 + idea.importance * 12 + Math.min(idea.resources, 10) * 2;
  const minHeight = 244 + idea.importance * 12 + idea.notes * 0.8;
  const style = {
    "--accent": colors.accent,
    "--accent-2": colors.accent2,
    "--texture": idea.texture,
    "--visual-height": `${visualHeight}px`,
    "--card-min-height": `${minHeight}px`,
    "--reveal-delay": `${index * 55}ms`,
    "--progress": `${idea.progress * 3.6}deg`,
  } as CSSProperties;

  function openCard(event: MouseEvent<HTMLElement>) {
    onOpen(idea, event.currentTarget.getBoundingClientRect());
  }

  return (
    <article
      className="idea-card"
      style={style}
      tabIndex={0}
      onClick={openCard}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen(idea, event.currentTarget.getBoundingClientRect());
        }
      }}
      aria-label={`Open ${idea.title} workspace`}
    >
      <div className="card-top">
        <span className="card-code">{idea.code}</span>
        <span className="progress-ring" aria-label={`${idea.progress}% complete`}>
          <span>{idea.progress}</span>
        </span>
      </div>

      <div className="card-body">
        <div className="card-header">
          <Badge tone="accent">{idea.status}</Badge>
          <span className={`pulse pulse-${idea.activity}`} aria-label={`Activity ${idea.activity}`} />
        </div>
        <h2 className="card-title">{idea.title}</h2>
        <p className="card-description">{idea.description}</p>
        <div className="tag-row">
          {idea.tags.map((tag) => (
            <Badge tone="muted" key={tag}>
              {tag}
            </Badge>
          ))}
        </div>
        <div className="meta-row">
          <span>
            <Layers3 size={15} aria-hidden="true" />
            {idea.resources} sources
          </span>
          <span>
            <FileText size={15} aria-hidden="true" />
            {idea.notes} notes
          </span>
          <span>{idea.updated}</span>
        </div>
      </div>

      <ArrowUpRight className="card-corner" size={22} aria-hidden="true" />
    </article>
  );
}
