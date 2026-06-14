import { FilePlus2, Link, ListTodo, Plus, X } from "lucide-react";
import { useState } from "react";
import { addResource, addTimelineEntry, uploadImageArtifact } from "../../api/workspace.ts";
import { createTask } from "../../lib/kanban.ts";
import type { KanbanTask } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";

interface StudioControlsOverlayProps {
  open: boolean;
  ideaId: string;
  onClose: () => void;
  onAddTask: (task: KanbanTask) => Promise<void> | void;
  onWorkspaceChange: () => Promise<void>;
}

type Mode = "task" | "link" | "diagram" | "log";

export function StudioControlsOverlay({ open, ideaId, onClose, onAddTask, onWorkspaceChange }: StudioControlsOverlayProps) {
  const [mode, setMode] = useState<Mode>("task");
  const [taskTitle, setTaskTitle] = useState("");
  const [linkValue, setLinkValue] = useState("");
  const [linkTitle, setLinkTitle] = useState("");
  const [diagramFile, setDiagramFile] = useState<File | null>(null);
  const [logText, setLogText] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!open) {
    return null;
  }

  async function runAction(action: () => Promise<void>, success: string) {
    setPending(true);
    setMessage(null);
    try {
      await action();
      await onWorkspaceChange();
      setMessage(success);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Action failed.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="studio-controls-overlay" role="dialog" aria-modal="true" aria-label="Studio controls">
      <div className="studio-controls-glass">
        <div className="overlay-heading">
          <div>
            <p className="eyebrow">Studio Controls</p>
            <h2>Capture the next useful action</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close studio controls">
            <X size={18} aria-hidden="true" />
          </Button>
        </div>

        <div className="studio-control-grid">
          <button type="button" className={mode === "task" ? "is-active" : ""} onClick={() => setMode("task")}>
            <ListTodo size={20} aria-hidden="true" />
            <span>Add task</span>
          </button>
          <button type="button" className={mode === "link" ? "is-active" : ""} onClick={() => setMode("link")}>
            <Link size={20} aria-hidden="true" />
            <span>Attach link</span>
          </button>
          <button type="button" className={mode === "diagram" ? "is-active" : ""} onClick={() => setMode("diagram")}>
            <FilePlus2 size={20} aria-hidden="true" />
            <span>New diagram</span>
          </button>
          <button type="button" className={mode === "log" ? "is-active" : ""} onClick={() => setMode("log")}>
            <Plus size={20} aria-hidden="true" />
            <span>Log update</span>
          </button>
        </div>

        {mode === "link" && (
          <div className="studio-form">
            <label className="field">
              <span>Link or source text</span>
              <input value={linkValue} onChange={(event) => setLinkValue(event.target.value)} placeholder="https://arxiv.org/abs/... or pasted source" />
            </label>
            <label className="field">
              <span>Title</span>
              <input value={linkTitle} onChange={(event) => setLinkTitle(event.target.value)} placeholder="Optional title" />
            </label>
            <Button
              variant="hot"
              disabled={pending}
              onClick={() =>
                runAction(async () => {
                  if (!linkValue.trim()) {
                    return;
                  }
                  await addResource(ideaId, linkValue.trim(), linkTitle.trim() || undefined);
                  setLinkValue("");
                  setLinkTitle("");
                }, "Linked evidence attached.")
              }
            >
              <Link size={17} aria-hidden="true" />
              <span>Attach resource</span>
            </Button>
          </div>
        )}

        {mode === "diagram" && (
          <div className="studio-form">
            <label className="field">
              <span>Upload image or diagram</span>
              <input type="file" accept="image/*" onChange={(event) => setDiagramFile(event.target.files?.[0] ?? null)} />
            </label>
            {diagramFile && <p className="studio-status">Ready: {diagramFile.name}</p>}
            <Button
              variant="hot"
              disabled={pending}
              onClick={() =>
                runAction(async () => {
                  if (!diagramFile) {
                    return;
                  }
                  await uploadImageArtifact(ideaId, diagramFile);
                  setDiagramFile(null);
                }, "Image uploaded, ingested, and added to gallery.")
              }
            >
              <FilePlus2 size={17} aria-hidden="true" />
              <span>Upload and ingest</span>
            </Button>
          </div>
        )}

        {mode === "log" && (
          <div className="studio-form">
            <label className="field">
              <span>Update</span>
              <textarea value={logText} onChange={(event) => setLogText(event.target.value)} rows={4} placeholder="What changed?" />
            </label>
            <Button
              variant="hot"
              disabled={pending}
              onClick={() =>
                runAction(async () => {
                  if (!logText.trim()) {
                    return;
                  }
                  await addTimelineEntry(ideaId, logText.trim(), "journal");
                  setLogText("");
                }, "Update logged.")
              }
            >
              <Plus size={17} aria-hidden="true" />
              <span>Log update</span>
            </Button>
          </div>
        )}

        {mode === "task" && (
          <div className="studio-form">
            <label className="add-task-control">
              <span>Add task</span>
              <input value={taskTitle} onChange={(event) => setTaskTitle(event.target.value)} placeholder="Name the next build step" />
            </label>
            <Button
              variant="hot"
              disabled={pending}
              onClick={() =>
                runAction(async () => {
                  if (!taskTitle.trim()) {
                    return;
                  }
                  await onAddTask(createTask(taskTitle, 2));
                  setTaskTitle("");
                }, "Task added.")
              }
            >
              <Plus size={17} aria-hidden="true" />
              <span>Add to To Do</span>
            </Button>
          </div>
        )}
        {message && <p className="studio-status">{message}</p>}
      </div>
    </div>
  );
}
