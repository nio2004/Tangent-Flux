import { Edit3, Eye, Save } from "lucide-react";
import { useState } from "react";
import { renderMarkdown } from "../../lib/markdown.ts";
import { Button } from "../ui/button.tsx";

interface MarkdownNotesProps {
  value: string;
  onSave: (value: string) => void;
}

export function MarkdownNotes({ value, onSave }: MarkdownNotesProps) {
  const [draft, setDraft] = useState(value);
  const [editing, setEditing] = useState(false);

  return (
    <section className="workspace-panel notes-shell" id="notes">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Markdown Notes</p>
          <h3>Working context</h3>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setEditing((current) => !current)}>
          {editing ? <Eye size={16} aria-hidden="true" /> : <Edit3 size={16} aria-hidden="true" />}
          <span>{editing ? "Preview" : "Edit"}</span>
        </Button>
      </div>

      {editing ? (
        <>
          <textarea
            className="notes-editor"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            aria-label="Edit markdown notes"
          />
          <Button
            variant="hot"
            onClick={() => {
              onSave(draft);
              setEditing(false);
            }}
          >
            <Save size={16} aria-hidden="true" />
            <span>Save notes</span>
          </Button>
        </>
      ) : (
        <div className="notes-rendered" dangerouslySetInnerHTML={{ __html: renderMarkdown(value) }} />
      )}
    </section>
  );
}
