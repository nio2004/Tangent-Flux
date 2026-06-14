import type { KanbanBoard, KanbanLaneId, KanbanTask } from "../types/idea.ts";

function slugifyTask(value: string) {
  const slug = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

  return slug || `task-${Date.now()}`;
}

export function createTask(title: string, points = 1): KanbanTask {
  const cleanTitle = title.trim().replace(/\s+/g, " ");

  return {
    id: slugifyTask(cleanTitle),
    title: cleanTitle,
    points: Math.max(1, Math.round(points)),
  };
}

export function moveTask(board: KanbanBoard, taskId: string, targetLane: KanbanLaneId): KanbanBoard {
  const next: KanbanBoard = {
    todo: [...board.todo],
    progress: [...board.progress],
    completed: [...board.completed],
  };

  let movingTask: KanbanTask | undefined;

  (Object.keys(next) as KanbanLaneId[]).forEach((laneId) => {
    next[laneId] = next[laneId].filter((task) => {
      if (task.id === taskId) {
        movingTask = task;
        return false;
      }

      return true;
    });
  });

  if (!movingTask) {
    return next;
  }

  next[targetLane] = [...next[targetLane], movingTask];
  return next;
}
