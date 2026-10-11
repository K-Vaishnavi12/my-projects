"use client";
import { useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragStartEvent,
  type DragEndEvent,
} from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { api } from "@/lib/api";
import { BoardColumn } from "./BoardColumn";
import { TaskCard } from "./TaskCard";
import { TaskDetailDialog } from "./TaskDetailDialog";
import { NewTaskDialog } from "./NewTaskDialog";
import type { Board, Task, ProjectMember } from "@/lib/types";

interface Props {
  board: Board;
  initialTasks: Record<number, Task[]>;
  members: ProjectMember[];
}

export function KanbanBoard({ board, initialTasks, members }: Props) {
  const [tasks, setTasks] = useState<Record<number, Task[]>>(initialTasks);
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [newTaskColumn, setNewTaskColumn] = useState<number | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const findColumnOfTask = useCallback(
    (taskId: number) => {
      for (const [colId, colTasks] of Object.entries(tasks)) {
        if (colTasks.some((t) => t.id === taskId)) return Number(colId);
      }
      return null;
    },
    [tasks]
  );

  const onDragStart = (event: DragStartEvent) => {
    const data = event.active.data.current;
    if (data?.type === "task") setActiveTask(data.task);
  };

  const onDragEnd = async (event: DragEndEvent) => {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const taskId = Number(active.id);
    const sourceColId = findColumnOfTask(taskId);
    if (!sourceColId) return;

    // Dropped on a column (empty area) or another task
    let destColId: number;
    const overData = over.data.current;
    if (overData?.type === "task") {
      destColId = findColumnOfTask(Number(over.id)) ?? sourceColId;
    } else {
      destColId = Number(over.id);
    }

    const sourceTasks = [...(tasks[sourceColId] ?? [])];
    const destTasks = sourceColId === destColId ? sourceTasks : [...(tasks[destColId] ?? [])];

    const oldIndex = sourceTasks.findIndex((t) => t.id === taskId);
    const newIndex = destTasks.findIndex((t) => t.id === Number(over.id));

    let updatedSource = sourceTasks;
    let updatedDest = destTasks;

    if (sourceColId === destColId) {
      updatedSource = arrayMove(sourceTasks, oldIndex, newIndex >= 0 ? newIndex : sourceTasks.length - 1);
      updatedDest = updatedSource;
    } else {
      const [moved] = updatedSource.splice(oldIndex, 1);
      const insertAt = newIndex >= 0 ? newIndex : updatedDest.length;
      updatedDest.splice(insertAt, 0, { ...moved, column_id: destColId });
    }

    setTasks((prev) => ({
      ...prev,
      [sourceColId]: updatedSource,
      [destColId]: updatedDest,
    }));

    try {
      await api.post(`/tasks/${taskId}/move`, {
        column_id: destColId,
        position: newIndex >= 0 ? newIndex : 0,
      });
    } catch {
      // Revert on failure
      setTasks(initialTasks);
    }
  };

  const handleTaskCreated = (task: Task) => {
    setTasks((prev) => ({
      ...prev,
      [task.column_id]: [...(prev[task.column_id] ?? []), task],
    }));
  };

  const handleTaskUpdated = (updated: Task) => {
    setSelectedTask(updated);
    setTasks((prev) => ({
      ...prev,
      [updated.column_id]: (prev[updated.column_id] ?? []).map((t) =>
        t.id === updated.id ? updated : t
      ),
    }));
  };

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4 min-h-[calc(100vh-200px)]">
          {board.columns.map((col) => (
            <BoardColumn
              key={col.id}
              column={col}
              tasks={tasks[col.id] ?? []}
              onAddTask={(colId) => setNewTaskColumn(colId)}
              onTaskClick={(task) => setSelectedTask(task)}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask && <TaskCard task={activeTask} onClick={() => {}} />}
        </DragOverlay>
      </DndContext>

      <NewTaskDialog
        open={newTaskColumn !== null}
        columnId={newTaskColumn}
        members={members}
        onClose={() => setNewTaskColumn(null)}
        onCreated={handleTaskCreated}
      />

      <TaskDetailDialog
        task={selectedTask}
        open={selectedTask !== null}
        onClose={() => setSelectedTask(null)}
        onUpdated={handleTaskUpdated}
      />
    </>
  );
}
