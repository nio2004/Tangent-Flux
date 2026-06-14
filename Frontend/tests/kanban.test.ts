import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { createTask, moveTask } from "../src/lib/kanban.ts";
import type { KanbanBoard } from "../src/types/idea.ts";

describe("kanban helpers", () => {
  it("creates a trimmed todo task with a stable slug and minimum point value", () => {
    assert.deepEqual(createTask("  Validate source review  ", 0), {
      id: "validate-source-review",
      title: "Validate source review",
      points: 1,
    });
  });

  it("moves a task to another lane without mutating the original board", () => {
    const board: KanbanBoard = {
      todo: [{ id: "map-flows", title: "Map flows", points: 2 }],
      progress: [],
      completed: [],
    };

    const next = moveTask(board, "map-flows", "progress");

    assert.equal(board.todo.length, 1);
    assert.equal(next.todo.length, 0);
    assert.deepEqual(next.progress, [{ id: "map-flows", title: "Map flows", points: 2 }]);
  });

  it("places the most recently moved task at the top of the target lane", () => {
    const board: KanbanBoard = {
      todo: [{ id: "map-flows", title: "Map flows", points: 2 }],
      progress: [{ id: "draft-brief", title: "Draft brief", points: 1 }],
      completed: [],
    };

    const next = moveTask(board, "map-flows", "progress");

    assert.deepEqual(next.progress.map((task) => task.id), ["map-flows", "draft-brief"]);
  });
});
