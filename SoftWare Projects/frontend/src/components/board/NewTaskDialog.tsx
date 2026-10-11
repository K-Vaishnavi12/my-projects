"use client";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Task, ProjectMember } from "@/lib/types";

const schema = z.object({
  title: z.string().min(1, "Title required"),
  description: z.string().optional(),
  assignee_id: z.string().optional(),
  due_date: z.string().optional(),
  priority: z.enum(["low", "medium", "high", "urgent"]).default("medium"),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  columnId: number | null;
  members: ProjectMember[];
  onClose: () => void;
  onCreated: (task: Task) => void;
}

export function NewTaskDialog({ open, columnId, members, onClose, onCreated }: Props) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { priority: "medium" },
  });

  const onSubmit = async (data: FormData) => {
    if (!columnId) return;
    const payload = {
      ...data,
      assignee_id: data.assignee_id ? Number(data.assignee_id) : undefined,
    };
    const { data: task } = await api.post<Task>(`/columns/${columnId}/tasks`, payload);
    onCreated(task);
    reset();
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 mt-2">
          <Input id="title" label="Title" placeholder="What needs to be done?" error={errors.title?.message} {...register("title")} />
          <div className="flex flex-col gap-1.5">
            <label htmlFor="description" className="text-sm font-medium">Description</label>
            <textarea
              id="description"
              rows={3}
              placeholder="Add more context…"
              className="rounded-md border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              {...register("description")}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="priority" className="text-sm font-medium">Priority</label>
              <select id="priority" className="rounded-md border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" {...register("priority")}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="assignee" className="text-sm font-medium">Assignee</label>
              <select id="assignee" className="rounded-md border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" {...register("assignee_id")}>
                <option value="">Unassigned</option>
                {members.map((m) => (
                  <option key={m.user.id} value={m.user.id}>{m.user.full_name}</option>
                ))}
              </select>
            </div>
          </div>
          <Input id="due_date" label="Due date" type="date" {...register("due_date")} />
          <div className="flex gap-2 justify-end pt-1">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit">Create task</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
