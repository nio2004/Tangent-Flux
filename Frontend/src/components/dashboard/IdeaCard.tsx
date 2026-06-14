import { ArrowUpRight, FileText, Layers3 } from "lucide-react";
import { motion } from "framer-motion";
import type { CSSProperties, MouseEvent } from "react";
import type { Idea } from "../../types/idea.ts";
import { Badge } from "../ui/badge.tsx";

interface IdeaCardProps {
  idea: Idea;
  index: number;
  onOpen: (idea: Idea, rect: DOMRect) => void;
}

const palette = [
  { accent: "var(--data-blue)", accent2: "var(--surface-chrome)" },
  { accent: "var(--data-red)", accent2: "var(--surface-chrome)" },
  { accent: "var(--accent-primary)", accent2: "var(--surface-chrome)" },
  { accent: "var(--text-muted)", accent2: "var(--data-blue)" },
];

export function IdeaCard({ idea, index, onOpen }: IdeaCardProps) {
  const colors = palette[index % palette.length];
  const style = {
    "--accent": colors.accent,
    "--accent-2": colors.accent2,
    "--texture": idea.texture,
    "--reveal-delay": `${index * 55}ms`,
    "--progress": `${idea.progress * 3.6}deg`,
  } as CSSProperties;

  function openCard(event: MouseEvent<HTMLElement>) {
    onOpen(idea, event.currentTarget.getBoundingClientRect());
  }

  return (
    <motion.article
      layout
      className="idea-card"
      style={style}
      tabIndex={0}
      onClick={openCard}
      initial={{ opacity: 0, y: 18, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.985 }}
      transition={{ delay: index * 0.045, duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen(idea, event.currentTarget.getBoundingClientRect());
        }
      }}
      aria-label={`Open ${idea.title} workspace`}
    >
      <div className="card-top">
        {idea.coverUrl && <img className="card-cover-image" src={idea.coverUrl} alt="" aria-hidden="true" />}
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
    </motion.article>
  );
}
