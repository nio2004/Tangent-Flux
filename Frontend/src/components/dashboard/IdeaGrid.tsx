import type { Idea } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";
import { IdeaCard } from "./IdeaCard.tsx";

interface IdeaGridProps {
  ideas: Idea[];
  onOpenIdea: (idea: Idea, rect: DOMRect) => void;
  onQuickAdd: () => void;
}

export function IdeaGrid({ ideas, onOpenIdea, onQuickAdd }: IdeaGridProps) {
  if (!ideas.length) {
    return (
      <section className="empty-state" aria-live="polite">
        <p className="eyebrow">No matching signals</p>
        <h2>Bring one thread back into view</h2>
        <p>Try a broader search, clear the active filter, or capture a fresh idea for later review.</p>
        <Button variant="chrome" onClick={onQuickAdd}>
          Capture new idea
        </Button>
      </section>
    );
  }

  return (
    <section className="masonry" aria-label="Idea board">
      {ideas.map((idea, index) => (
        <IdeaCard key={idea.id} idea={idea} index={index} onOpen={onOpenIdea} />
      ))}
    </section>
  );
}
