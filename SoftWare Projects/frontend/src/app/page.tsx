import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b bg-white/70 backdrop-blur">
        <span className="text-xl font-bold text-indigo-600">TaskFlow</span>
        <div className="flex gap-3">
          <Link href="/login">
            <Button variant="ghost">Sign in</Button>
          </Link>
          <Link href="/register">
            <Button>Get started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-20">
        <span className="mb-4 inline-block rounded-full bg-indigo-100 px-4 py-1 text-sm font-medium text-indigo-700">
          Free for student teams
        </span>
        <h1 className="text-5xl font-extrabold tracking-tight text-gray-900 max-w-3xl leading-tight">
          Your team&rsquo;s work, <span className="text-indigo-600">beautifully organized</span>
        </h1>
        <p className="mt-6 max-w-xl text-lg text-gray-600">
          TaskFlow brings Kanban boards, task tracking, comments, and collaboration together in one clean workspace — built for student teams and early-stage startups.
        </p>
        <div className="mt-8 flex gap-4 flex-wrap justify-center">
          <Link href="/register">
            <Button size="lg">Start for free</Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline">Sign in</Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 px-8 pb-20 max-w-5xl mx-auto w-full">
        {[
          { icon: "📋", title: "Kanban Boards", desc: "Drag and drop tasks across To Do, In Progress, and Done columns." },
          { icon: "👥", title: "Team Collaboration", desc: "Invite members, assign tasks, leave comments, and stay in sync." },
          { icon: "🔍", title: "Smart Filters", desc: "Search and filter by assignee, priority, label, or due date." },
        ].map((f) => (
          <div key={f.title} className="rounded-xl border bg-white p-6 shadow-sm">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-semibold text-gray-900">{f.title}</h3>
            <p className="mt-1 text-sm text-gray-500">{f.desc}</p>
          </div>
        ))}
      </section>

      <footer className="text-center py-6 text-sm text-gray-400 border-t">
        © 2024 TaskFlow. Built with FastAPI + Next.js.
      </footer>
    </main>
  );
}
