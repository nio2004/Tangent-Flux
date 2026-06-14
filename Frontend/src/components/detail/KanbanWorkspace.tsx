import { Maximize2, X } from "lucide-react";
import { CSSProperties, DragEvent, useState } from "react";
import type { KanbanBoard, KanbanLaneId, KanbanTask } from "../../types/idea.ts";
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
  const [draggingTask, setDraggingTask] = useState<string | null>(null);

  function handleDrop(event: DragEvent<HTMLElement>, laneId: KanbanLaneId) {
    event.preventDefault();
    const taskId = event.dataTransfer.getData("text/plain") || draggingTask;
    if (taskId) {
      onMoveTask(taskId, laneId);
    }
    setDraggingTask(null);
  }

  function renderTaskCard(task: KanbanTask, laneId: KanbanLaneId, compact = false) {
    return (
      <article
        className={[
          compact ? "task-card task-card-compact" : "task-card",
          draggingTask === task.id ? "is-dragging" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        key={task.id}
        draggable
        onClick={(event) => event.stopPropagation()}
        onDragStartCapture={(event) => {
          setDraggingTask(task.id);
          event.dataTransfer.setData("text/plain", task.id);
          event.dataTransfer.effectAllowed = "move";
        }}
        onDragEndCapture={() => setDraggingTask(null)}
      >
        <strong>{task.title}</strong>
        <div className="task-row">
          <small>{task.points} pts</small>
          <small>{laneLabels[laneId]}</small>
        </div>
        {!compact && (
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
    );
  }

  const previewBoard = (
    <div className="kanban kanban-preview-board" aria-label="Build task board preview">
      {laneIds.map((laneId) => (
        <section
          className={draggingTask ? "lane lane-preview is-drop-ready" : "lane lane-preview"}
          key={laneId}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => handleDrop(event, laneId)}
        >
          <div className="lane-heading">
            <h4>{laneLabels[laneId]}</h4>
            <span>{board[laneId].length}</span>
          </div>
          <div className="task-stack">
            {board[laneId].slice(0, 4).map((task, index) => (
              <div
                className={index === 0 ? "task-stack-layer active" : "task-stack-layer"}
                key={task.id}
                style={{ "--stack-index": index } as CSSProperties}
              >
                {renderTaskCard(task, laneId, true)}
              </div>
            ))}
            {board[laneId].length === 0 ? <p className="empty-lane">Drop tasks here</p> : null}
          </div>
        </section>
      ))}
    </div>
  );

  const expandedBoard = (
    <div className="kanban kanban-expanded" aria-label="Expanded build task board">
      {laneIds.map((laneId) => (
        <section
          className={draggingTask ? "lane is-drop-ready" : "lane"}
          key={laneId}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => handleDrop(event, laneId)}
        >
          <div className="lane-heading">
            <h4>{laneLabels[laneId]}</h4>
            <span>{board[laneId].length}</span>
          </div>
          <div className="expanded-task-list">
            {board[laneId].map((task) => renderTaskCard(task, laneId))}
            {board[laneId].length === 0 ? <p className="empty-lane">Drop tasks here</p> : null}
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
        <div className="kanban-preview-frame">
          {previewBoard}
        </div>
        <button className="kanban-expand-button" type="button" onClick={() => onExpandedChange(true)}>
          Open board
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
              <Button variant="ghost" size="icon" onClick={() => onExpandedChange(false)} aria-label="Close Kanban board">
                <X size={18} aria-hidden="true" />
              </Button>
            </div>
            {expandedBoard}
          </div>
        </div>
      )}
    </>
  );
}
