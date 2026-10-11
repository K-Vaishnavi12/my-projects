"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { NewProjectDialog } from "@/components/projects/NewProjectDialog";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, fetchMe, isLoading } = useAuthStore();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [showNew, setShowNew] = useState(false);

  useEffect(() => {
    fetchMe().then(() => {
      if (!useAuthStore.getState().user) router.replace("/login");
    });
  }, [fetchMe, router]);

  useEffect(() => {
    if (user) {
      api.get<Project[]>("/projects").then(({ data }) => setProjects(data));
    }
  }, [user]);

  if (isLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar
        projects={projects}
        onNewProject={() => setShowNew(true)}
      />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      <NewProjectDialog
        open={showNew}
        onClose={() => setShowNew(false)}
        onCreated={(p) => {
          setProjects((prev) => [...prev, p]);
          router.push(`/projects/${p.id}`);
        }}
      />
    </div>
  );
}
