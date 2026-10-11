"use client";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { MessageSquare, Paperclip, Calendar } from "lucide-react";
import { format } from "date-fns";
import { cn, PRIORITY_COLORS, PRIORITY_LABELS } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Task } from "@/lib/types";

interface Props {
  task: Task;
  onClick: () => void;
}

export function TaskCard({ task, onClick }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
    data: { type: "task", task },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const isOverdue =
    task.due_date && new Date(task.due_date) < new Date() && !isDragging;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className={cn(
        "group rounded-lg border bg-white p-3 shadow-sm cursor-pointer hover:border-indigo-300 hover:shadow-md transition-all select-none",
        isDragging && "opacity-50 rotate-1 shadow-lg"
      )}
    >
      {/* Labels */}
      {task.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {task.labels.map((l) => (
            <span
              key={l.id}
              className="inline-block rounded-full px-2 py-0.5 text-xs font-medium text-white"
              style={{ backgroundColor: l.color }}
            >
              {l.name}
            </span>
          ))}
        </div>
      )}

      <p className="text-sm font-medium text-gray-900 leading-snug">{task.title}</p>

      {/* Meta row */}
      <div className="mt-2 flex items-center gap-2 flex-wrap">
        <Badge className={cn("text-xs", PRIORITY_COLORS[task.priority])}>
          {PRIORITY_LABELS[task.priority]}
        </Badge>

        {task.due_date && (
          <span
            className={cn(
              "flex items-center gap-1 text-xs",
              isOverdue ? "text-red-600 font-medium" : "text-gray-400"
            )}
          >
            <Calendar className="h-3 w-3" />
            {format(new Date(task.due_date), "MMM d")}
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="mt-3 flex items-center justify-between">
        {task.assignee ? (
          <div
            className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-semibold text-indigo-700"
            title={task.assignee.full_name}
          >
            {task.assignee.full_name[0].toUpperCase()}
          </div>
        ) : (
          <div />
        )}

        <div className="flex items-center gap-3 text-gray-400 text-xs">
          {task.comments?.length > 0 && (
            <span className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              {task.comments.length}
            </span>
          )}
          {task.attachments?.length > 0 && (
            <span className="flex items-center gap-1">
              <Paperclip className="h-3 w-3" />
              {task.attachments.length}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
