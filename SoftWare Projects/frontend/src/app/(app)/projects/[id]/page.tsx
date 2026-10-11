"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Plus, Users, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toaster";
import type { Project, Board } from "@/lib/types";
import { useAuthStore } from "@/store/auth";

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuthStore();
  const { toast } = useToast();
  const [project, setProject] = useState<Project | null>(null);
  const [boards, setBoards] = useState<Board[]>([]);
  const [creatingBoard, setCreatingBoard] = useState(false);
  const [newBoardName, setNewBoardName] = useState("");

  useEffect(() => {
    api.get<Project>(`/projects/${id}`).then(({ data }) => setProject(data));
    api.get<Board[]>(`/projects/${id}/boards`).then(({ data }) => setBoards(data));
  }, [id]);

  const createBoard = async () => {
    if (!newBoardName.trim()) return;
    const { data } = await api.post<Board>(`/projects/${id}/boards`, { name: newBoardName });
    setBoards((prev) => [...prev, data]);
    setNewBoardName("");
    setCreatingBoard(false);
    router.push(`/projects/${id}/boards/${data.id}`);
  };

  const deleteProject = async () => {
    if (!confirm("Delete this project and all its data? This cannot be undone.")) return;
    await api.delete(`/projects/${id}`);
    toast({ title: "Project deleted" });
    router.push("/dashboard");
  };

  if (!project) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  const isOwner = project.owner_id === user?.id;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-center gap-4">
          <div
            className="h-12 w-12 rounded-xl flex items-center justify-center text-white font-bold text-lg"
            style={{ backgroundColor: project.color }}
          >
            {project.name[0].toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
            {project.description && <p className="text-gray-500 text-sm mt-0.5">{project.description}</p>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-sm text-gray-400">
            <Users className="h-4 w-4" />
            {project.members.length}
          </div>
          {isOwner && (
            <Button variant="destructive" size="sm" onClick={deleteProject}>
              <Trash2 className="h-3.5 w-3.5 mr-1" />
              Delete
            </Button>
          )}
        </div>
      </div>

      {/* Boards */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Boards</h2>
        <Button size="sm" onClick={() => setCreatingBoard(true)}>
          <Plus className="h-3.5 w-3.5 mr-1" />
          New board
        </Button>
      </div>

      {creatingBoard && (
        <div className="mb-4 flex gap-2">
          <input
            autoFocus
            value={newBoardName}
            onChange={(e) => setNewBoardName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && createBoard()}
            placeholder="Board name, e.g. Sprint 1"
            className="flex-1 rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <Button size="sm" onClick={createBoard}>Create</Button>
          <Button size="sm" variant="outline" onClick={() => setCreatingBoard(false)}>Cancel</Button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {boards.map((b) => (
          <Link
            key={b.id}
            href={`/projects/${id}/boards/${b.id}`}
            className="rounded-xl border bg-white p-5 hover:border-indigo-200 hover:shadow-md transition-all"
          >
            <p className="font-semibold text-gray-900">{b.name}</p>
            <p className="text-sm text-gray-400 mt-1">{b.columns.length} columns</p>
          </Link>
        ))}

        {boards.length === 0 && !creatingBoard && (
          <div className="col-span-3 rounded-xl border-2 border-dashed p-10 text-center text-gray-300">
            No boards yet. Create one to get started.
          </div>
        )}
      </div>

      {/* Members */}
      <div className="mt-10">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Members ({project.members.length})
        </h2>
        <div className="flex flex-wrap gap-3">
          {project.members.map((m) => (
            <div key={m.id} className="flex items-center gap-2 rounded-full border bg-white px-3 py-1.5">
              <div className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-semibold text-indigo-700">
                {m.user.full_name[0].toUpperCase()}
              </div>
              <span className="text-sm">{m.user.full_name}</span>
              <span className="text-xs text-gray-400 capitalize">{m.role}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
