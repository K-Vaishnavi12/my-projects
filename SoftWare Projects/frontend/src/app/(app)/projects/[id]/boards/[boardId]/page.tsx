"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, Search } from "lucide-react";
import { api } from "@/lib/api";
import { KanbanBoard } from "@/components/board/KanbanBoard";
import type { Board, Task, Project } from "@/lib/types";

export default function BoardPage() {
  const { id, boardId } = useParams<{ id: string; boardId: string }>();
  const [board, setBoard] = useState<Board | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [tasksByColumn, setTasksByColumn] = useState<Record<number, Task[]>>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<Project>(`/projects/${id}`),
      api.get<Board>(`/boards/${boardId}`).catch(() =>
        // boards endpoint by ID not explicitly in routes; fetch from project boards
        api.get<Board[]>(`/projects/${id}/boards`).then(({ data }) => ({
          data: data.find((b) => b.id === Number(boardId))!,
        }))
      ),
    ]).then(([projRes, boardRes]) => {
      setProject(projRes.data);
      const b = boardRes.data as Board;
      setBoard(b);
      // Fetch tasks per column
      return Promise.all(
        b.columns.map((col) =>
          api.get<Task[]>(`/columns/${col.id}/tasks`).then(({ data }) => ({ colId: col.id, tasks: data }))
        )
      );
    }).then((colTasks) => {
      const map: Record<number, Task[]> = {};
      colTasks.forEach(({ colId, tasks }) => { map[colId] = tasks; });
      setTasksByColumn(map);
    }).finally(() => setLoading(false));
  }, [id, boardId]);

  if (loading || !board || !project) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  const filteredTasks = searchQuery
    ? Object.fromEntries(
        Object.entries(tasksByColumn).map(([colId, tasks]) => [
          colId,
          tasks.filter(
            (t) =>
              t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
              t.description?.toLowerCase().includes(searchQuery.toLowerCase())
          ),
        ])
      )
    : tasksByColumn;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b bg-white px-8 py-4 flex items-center gap-4">
        <Link
          href={`/projects/${id}`}
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-gray-700"
        >
          <ChevronLeft className="h-4 w-4" />
          {project.name}
        </Link>
        <span className="text-gray-300">/</span>
        <h1 className="text-lg font-semibold text-gray-900">{board.name}</h1>

        {/* Search */}
        <div className="ml-auto flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm w-64">
          <Search className="h-4 w-4 text-gray-400 shrink-0" />
          <input
            placeholder="Search tasks…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent focus:outline-none text-sm"
          />
        </div>
      </div>

      {/* Board */}
      <div className="flex-1 overflow-auto p-6">
        <KanbanBoard
          board={board}
          initialTasks={filteredTasks as Record<number, Task[]>}
          members={project.members}
        />
      </div>
    </div>
  );
}
