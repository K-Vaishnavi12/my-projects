"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { Project } from "@/lib/types";
import { PRIORITY_COLORS } from "@/lib/utils";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.get<Project[]>("/projects").then(({ data }) => setProjects(data));
  }, []);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Good {getGreeting()}, {user?.full_name?.split(" ")[0]} 👋
        </h1>
        <p className="text-gray-500 mt-1">Here&rsquo;s what&rsquo;s happening across your projects.</p>
      </div>

      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        Your projects ({projects.length})
      </h2>

      {projects.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed p-12 text-center">
          <p className="text-gray-400">No projects yet.</p>
          <p className="text-sm text-gray-300 mt-1">Click the + in the sidebar to create one.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="group rounded-xl border bg-white p-5 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all"
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="h-9 w-9 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                  style={{ backgroundColor: p.color }}
                >
                  {p.name[0].toUpperCase()}
                </div>
                <div>
                  <p className="font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors">
                    {p.name}
                  </p>
                  <p className="text-xs text-gray-400">{p.members.length} member{p.members.length !== 1 ? "s" : ""}</p>
                </div>
              </div>
              {p.description && (
                <p className="text-sm text-gray-500 line-clamp-2">{p.description}</p>
              )}
              <p className="text-xs text-gray-300 mt-3">
                Updated {format(new Date(p.updated_at), "MMM d")}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 17) return "afternoon";
  return "evening";
}
