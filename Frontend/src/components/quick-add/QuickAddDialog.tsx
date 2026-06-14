import Dialog from "@mui/material/Dialog";
import { Plus, X } from "lucide-react";
import { FormEvent, useState } from "react";
import { initials, slugify } from "../../lib/utils.ts";
import type { Idea } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";

interface QuickAddDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (idea: Idea) => void;
}

export function QuickAddDialog({ open, onClose, onCreate }: QuickAddDialogProps) {
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [note, setNote] = useState("");
  const [tags, setTags] = useState("");

  function reset() {
    setTitle("");
    setSource("");
    setNote("");
    setTags("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanTitle = title.trim();
    if (!cleanTitle) {
      return;
    }

    const tagList = tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    onCreate({
      id: `${slugify(cleanTitle)}-${Date.now()}`,
      title: cleanTitle,
      status: "Capture",
      description: note.trim() || "Fresh capture ready to be expanded into notes, sources, and build tasks.",
      tags: tagList.length ? tagList : ["Capture"],
      progress: 12,
      resources: source.trim() ? 1 : 0,
      notes: note.trim() ? 1 : 0,
      updated: "Just now",
      activity: "new",
      code: initials(cleanTitle),
      importance: tagList.some((tag) => tag.toLowerCase() === "pinned") ? 4 : 2,
      texture:
        "linear-gradient(135deg, rgba(22,140,255,.82), rgba(216,226,239,.32)), radial-gradient(circle at 74% 30%, rgba(255,209,47,.32), transparent 24%)",
      problem: source.trim()
        ? `Initial source captured from ${source.trim()}.`
        : "This idea needs a problem statement, source stack, and first build task.",
      initialSource: source.trim() || undefined,
      quickNote: note.trim() || undefined,
    });
    reset();
    onClose();
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ className: "modal-card" }}
      aria-labelledby="quick-add-title"
    >
      <form onSubmit={handleSubmit}>
        <div className="modal-heading">
          <div>
            <p className="eyebrow">Quick Add</p>
            <h2 id="quick-add-title">Capture a signal</h2>
          </div>
          <Button variant="ghost" size="icon" type="button" onClick={onClose} aria-label="Close quick add">
            <X size={18} aria-hidden="true" />
          </Button>
        </div>

        <div className="modal-grid">
          <label className="field">
            <span>Title *</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} required autoFocus />
          </label>
          <label className="field">
            <span>Link or source</span>
            <input value={source} onChange={(event) => setSource(event.target.value)} />
          </label>
          <label className="field field-wide">
            <span>Quick note</span>
            <textarea value={note} onChange={(event) => setNote(event.target.value)} rows={4} />
          </label>
          <label className="field field-wide">
            <span>Tags</span>
            <input
              value={tags}
              onChange={(event) => setTags(event.target.value)}
              placeholder="AI, Research, Pinned"
            />
          </label>
        </div>

        <div className="modal-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="hot">
            <Plus size={17} aria-hidden="true" />
            <span>Add idea</span>
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
