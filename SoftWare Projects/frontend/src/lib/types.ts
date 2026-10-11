export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
}

export interface ProjectMember {
  id: number;
  user: User;
  role: "owner" | "admin" | "member" | "viewer";
  joined_at: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  color: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
  members: ProjectMember[];
}

export interface Column {
  id: number;
  board_id: number;
  name: string;
  position: number;
  color: string;
}

export interface Board {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  created_at: string;
  columns: Column[];
}

export type Priority = "low" | "medium" | "high" | "urgent";

export interface Label {
  id: number;
  name: string;
  color: string;
}

export interface Attachment {
  id: number;
  filename: string;
  url: string;
  created_at: string;
}

export interface Comment {
  id: number;
  content: string;
  author: User;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  column_id: number;
  title: string;
  description?: string;
  assignee?: User;
  due_date?: string;
  priority: Priority;
  position: number;
  created_at: string;
  updated_at: string;
  labels: Label[];
  attachments: Attachment[];
  comments: Comment[];
}
