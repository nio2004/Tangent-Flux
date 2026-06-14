import { Maximize2 } from "lucide-react";
import type { KanbanBoard, KanbanLaneId } from "../../types/idea.ts";
import { Button } from "../ui/button.tsx";

interface KanbanWorkspaceProps {
  board: KanbanBoard;
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
  onMoveTask: (taskId: string, lane: KanbanLaneId) => void;
}

const laneLabels: Record<KanbanLaneId, string> = {
  todo: "To Do",
  progress: "In Progress",
  completed: "Completed",
};

const laneIds: KanbanLaneId[] = ["todo", "progress", "completed"];

export function KanbanWorkspace({ board, expanded, onExpandedChange, onMoveTask }: KanbanWorkspaceProps) {
  const boardView = (
    <div className="kanban" aria-label="Build task board">
      {laneIds.map((laneId) => (
        <section className="lane" key={laneId}>
          <div className="lane-heading">
            <h4>{laneLabels[laneId]}</h4>
            <span>{board[laneId].length}</span>
          </div>
          <div className="task-stack">
            {board[laneId].map((task) => (
              <article className="task-card" key={task.id}>
                <strong>{task.title}</strong>
                <small>{task.points} pts</small>
                {expanded && (
                  <div className="task-move-row">
                    {laneIds.map((targetLane) => (
                      <button
                        key={targetLane}
                        type="button"
                        onClick={() => onMoveTask(task.id, targetLane)}
                        disabled={targetLane === laneId}
                      >
                        {laneLabels[targetLane]}
                      </button>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );

  return (
    <>
      <section className="workspace-panel kanban-preview" id="tasks">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Build Tasks</p>
            <h3>Task workspace</h3>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onExpandedChange(true)}>
            <Maximize2 size={16} aria-hidden="true" />
            <span>Expand</span>
          </Button>
        </div>
        <button
          className="kanban-preview-button"
          type="button"
          onClick={() => onExpandedChange(true)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onExpandedChange(true);
            }
          }}
          aria-label="Open expanded Kanban board"
        >
          {boardView}
        </button>
      </section>

      {expanded && (
        <div className="kanban-overlay" role="dialog" aria-modal="true" aria-label="Expanded Kanban board">
          <div className="kanban-glass">
            <div className="overlay-heading">
              <div>
                <p className="eyebrow">Expanded Board</p>
                <h2>Move work through review</h2>
              </div>
              <Button variant="ghost" onClick={() => onExpandedChange(false)}>
                Close
              </Button>
            </div>
            {boardView}
          </div>
        </div>
      )}
    </>
  );
}
