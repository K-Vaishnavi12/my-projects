"use client";
import { useState } from "react";
import { format } from "date-fns";
import { Send, Paperclip, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PRIORITY_COLORS, PRIORITY_LABELS, cn } from "@/lib/utils";
import type { Task, Comment } from "@/lib/types";
import { useAuthStore } from "@/store/auth";

interface Props {
  task: Task | null;
  open: boolean;
  onClose: () => void;
  onUpdated: (task: Task) => void;
}

export function TaskDetailDialog({ task, open, onClose, onUpdated }: Props) {
  const { user } = useAuthStore();
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [attachUrl, setAttachUrl] = useState("");
  const [attachName, setAttachName] = useState("");

  if (!task) return null;

  const addComment = async () => {
    if (!comment.trim()) return;
    setSubmitting(true);
    try {
      const { data: newComment } = await api.post<Comment>(`/tasks/${task.id}/comments`, {
        content: comment,
      });
      onUpdated({ ...task, comments: [...task.comments, newComment] });
      setComment("");
    } finally {
      setSubmitting(false);
    }
  };

  const deleteComment = async (commentId: number) => {
    await api.delete(`/comments/${commentId}`);
    onUpdated({ ...task, comments: task.comments.filter((c) => c.id !== commentId) });
  };

  const addAttachment = async () => {
    if (!attachUrl.trim() || !attachName.trim()) return;
    const { data } = await api.post(`/tasks/${task.id}/attachments`, {
      filename: attachName,
      url: attachUrl,
    });
    onUpdated({ ...task, attachments: [...task.attachments, data] });
    setAttachUrl("");
    setAttachName("");
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg pr-6">{task.title}</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-3 gap-6 mt-2">
          {/* Main */}
          <div className="col-span-2 flex flex-col gap-4">
            {task.description && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Description</p>
                <p className="text-sm text-gray-700 whitespace-pre-line">{task.description}</p>
              </div>
            )}

            {/* Labels */}
            {task.labels.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Labels</p>
                <div className="flex gap-1 flex-wrap">
                  {task.labels.map((l) => (
                    <span
                      key={l.id}
                      className="rounded-full px-2 py-0.5 text-xs font-medium text-white"
                      style={{ backgroundColor: l.color }}
                    >
                      {l.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Attachments */}
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Attachments</p>
              {task.attachments.map((a) => (
                <a
                  key={a.id}
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-indigo-600 hover:underline"
                >
                  <Paperclip className="h-3.5 w-3.5" />
                  {a.filename}
                </a>
              ))}
              <div className="flex gap-2 mt-2">
                <Input placeholder="File name" value={attachName} onChange={(e) => setAttachName(e.target.value)} className="text-xs" />
                <Input placeholder="URL" value={attachUrl} onChange={(e) => setAttachUrl(e.target.value)} className="text-xs" />
                <Button size="sm" variant="outline" onClick={addAttachment}>Add</Button>
              </div>
            </div>

            {/* Comments */}
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase mb-2">
                Comments ({task.comments.length})
              </p>
              <div className="flex flex-col gap-3">
                {task.comments.map((c) => (
                  <div key={c.id} className="flex gap-2">
                    <div className="h-7 w-7 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-semibold text-indigo-700 shrink-0">
                      {c.author.full_name[0].toUpperCase()}
                    </div>
                    <div className="flex-1 rounded-lg bg-gray-50 px-3 py-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-gray-700">{c.author.full_name}</span>
                        <div className="flex items-center gap-1 text-xs text-gray-400">
                          <span>{format(new Date(c.created_at), "MMM d, h:mm a")}</span>
                          {c.author.id === user?.id && (
                            <button onClick={() => deleteComment(c.id)} className="hover:text-red-500">
                              <Trash2 className="h-3 w-3" />
                            </button>
                          )}
                        </div>
                      </div>
                      <p className="text-sm mt-0.5 text-gray-600">{c.content}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-3 flex gap-2">
                <input
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && addComment()}
                  placeholder="Write a comment…"
                  className="flex-1 rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
                <Button size="icon" onClick={addComment} disabled={submitting || !comment.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="flex flex-col gap-4 text-sm">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Priority</p>
              <Badge className={cn(PRIORITY_COLORS[task.priority])}>
                {PRIORITY_LABELS[task.priority]}
              </Badge>
            </div>
            {task.assignee && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Assignee</p>
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-semibold text-indigo-700">
                    {task.assignee.full_name[0].toUpperCase()}
                  </div>
                  <span className="text-sm">{task.assignee.full_name}</span>
                </div>
              </div>
            )}
            {task.due_date && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Due date</p>
                <p>{format(new Date(task.due_date), "MMM d, yyyy")}</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
