"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, LogOut, Plus, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import type { Project } from "@/lib/types";

interface SidebarProps {
  projects: Project[];
  onNewProject: () => void;
}

export function Sidebar({ projects, onNewProject }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <aside className="w-60 shrink-0 border-r bg-white flex flex-col h-screen sticky top-0">
      {/* Brand */}
      <div className="px-5 py-4 border-b">
        <span className="text-lg font-bold text-indigo-600">TaskFlow</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-3 flex flex-col gap-1">
        <Link
          href="/dashboard"
          className={cn(
            "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
            pathname === "/dashboard"
              ? "bg-indigo-50 text-indigo-700"
              : "text-gray-600 hover:bg-gray-100"
          )}
        >
          <LayoutDashboard className="h-4 w-4" />
          Dashboard
        </Link>

        {/* Projects */}
        <div className="mt-4">
          <div className="flex items-center justify-between px-3 mb-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Projects</span>
            <button
              onClick={onNewProject}
              className="rounded p-0.5 hover:bg-gray-100 text-gray-400 hover:text-gray-700"
              aria-label="New project"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className={cn(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                pathname.startsWith(`/projects/${p.id}`)
                  ? "bg-indigo-50 text-indigo-700 font-medium"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <span
                className="h-2 w-2 rounded-full shrink-0"
                style={{ backgroundColor: p.color }}
              />
              <span className="truncate">{p.name}</span>
            </Link>
          ))}
        </div>
      </nav>

      {/* User */}
      <div className="border-t p-3 flex items-center gap-2">
        <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-sm font-semibold shrink-0">
          {user?.full_name?.[0]?.toUpperCase() ?? "U"}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{user?.full_name}</p>
          <p className="text-xs text-gray-400 truncate">{user?.email}</p>
        </div>
        <button onClick={handleLogout} className="text-gray-400 hover:text-gray-700" aria-label="Logout">
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </aside>
  );
}
