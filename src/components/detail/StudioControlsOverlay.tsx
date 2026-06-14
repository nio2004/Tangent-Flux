import { FilePlus2, Link, Plus, X } from "lucide-react";
import { useState } from "react";
import { createTask } from "../../lib/kanban.ts";
import type { KanbanTask } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";

interface StudioControlsOverlayProps {
  open: boolean;
  onClose: () => void;
  onAddTask: (task: KanbanTask) => void;
}

export function StudioControlsOverlay({ open, onClose, onAddTask }: StudioControlsOverlayProps) {
  const [taskTitle, setTaskTitle] = useState("");

  if (!open) {
    return null;
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
          <button type="button">
            <Link size={20} aria-hidden="true" />
            <span>Attach link</span>
          </button>
          <button type="button">
            <FilePlus2 size={20} aria-hidden="true" />
            <span>New diagram</span>
          </button>
          <button type="button">
            <Plus size={20} aria-hidden="true" />
            <span>Log update</span>
          </button>
        </div>

        <label className="add-task-control">
          <span>Add task</span>
          <input
            value={taskTitle}
            onChange={(event) => setTaskTitle(event.target.value)}
            placeholder="Name the next build step"
          />
        </label>
        <Button
          variant="hot"
          onClick={() => {
            if (!taskTitle.trim()) {
              return;
            }
            onAddTask(createTask(taskTitle, 2));
            setTaskTitle("");
          }}
        >
          <Plus size={17} aria-hidden="true" />
          <span>Add to To Do</span>
        </Button>
      </div>
    </div>
  );
}
