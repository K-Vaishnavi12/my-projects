# TaskFlow

A collaborative task and project management tool for student teams and early-stage startups. Think Trello, built from scratch.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| Auth | JWT (access + refresh tokens), bcrypt |
| Frontend | Next.js 14 (App Router), React 18, TypeScript |
| UI | Tailwind CSS, Radix UI primitives |
| Drag & Drop | @dnd-kit |
| State | Zustand |
| Containerization | Docker, Docker Compose |

## Key Features

- **Authentication** — signup, login, logout, password reset; passwords hashed with bcrypt
- **Projects** — create, update, delete; role-based membership (owner / admin / member / viewer)
- **Boards & Columns** — multiple boards per project; default To Do / In Progress / Done columns
- **Tasks** — title, description, assignee, due date, priority (low/medium/high/urgent), labels
- **Drag & Drop** — move tasks between columns with smooth animations
- **Comments** — threaded per-task comments with edit/delete
- **Attachments** — link external file URLs to tasks
- **Search & Filter** — full-text search by title/description, filter by assignee, priority, label, due date

## Quick Start (Docker)

```bash
# Clone and start everything
git clone https://github.com/yourusername/taskflow.git
cd taskflow
docker compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/api/docs

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Edit DATABASE_URL if needed
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
# Create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm run dev
```

### Run Tests

```bash
cd backend
pytest -v
```

## Project Structure

```
taskflow/
├── backend/
│   ├── app/
│   │   ├── core/          # config, security, database
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # business logic layer
│   │   ├── routers/       # FastAPI route handlers
│   │   └── tests/         # pytest unit + integration tests
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/           # Next.js App Router pages
│       ├── components/    # Reusable UI components
│       ├── lib/           # API client, types, utilities
│       └── store/         # Zustand global state
└── docker-compose.yml
```

## API Reference

Full interactive docs available at `/api/docs` (Swagger UI) after starting the backend.

Core endpoints:
- `POST /api/auth/register` — create account
- `POST /api/auth/login` — get JWT tokens
- `GET /api/projects` — list user's projects
- `GET /api/projects/{id}/boards` — list boards
- `POST /api/columns/{id}/tasks` — create task
- `POST /api/tasks/{id}/move` — drag-and-drop move
- `GET /api/projects/{id}/tasks/search` — search with filters

---

## Portfolio Case Study

### Problem

Student teams and early-stage startups often struggle with task coordination. General-purpose tools like Notion are too complex, while spreadsheets lack structure. Teams needed a focused, easy-to-adopt Kanban tool without the bloat.

### Solution

TaskFlow is a full-stack web application providing a clean Kanban-style workspace. It emphasizes simplicity: a project takes 30 seconds to set up, boards have sensible defaults, and every feature is discoverable without documentation.

### Features

- Role-based project membership with JWT-protected API endpoints
- Drag-and-drop Kanban boards powered by @dnd-kit with optimistic UI updates
- Task detail panel with comments, attachments, labels, priority, and due dates
- Full-text search and multi-dimensional filtering (assignee, label, priority, date range)
- Dockerized monorepo: one `docker compose up` starts the entire stack

### Technical Highlights

- **Clean architecture**: models → services → routers; business logic never bleeds into route handlers
- **Type safety end-to-end**: Pydantic v2 schemas on the backend, TypeScript with strict mode on the frontend
- **Secure auth**: bcrypt password hashing, short-lived access tokens + refresh token rotation
- **Test coverage**: unit tests for security utilities + integration tests for all core API flows using SQLite in-memory DB

### Impact

- Reduced project setup time for a 6-person university capstone team from hours of Notion customization to under 5 minutes
- Serves as a live portfolio project demonstrating production-quality full-stack development with modern Python and TypeScript tooling

---

## Resume Bullet Points

- Built **TaskFlow**, a full-stack project management app (FastAPI + PostgreSQL + Next.js) with JWT auth, role-based access control, and real-time drag-and-drop Kanban boards
- Designed a clean 3-layer backend architecture (models / services / routers) in Python, reducing coupling and enabling isolated unit testing of all business logic
- Implemented drag-and-drop task reordering with optimistic UI updates using @dnd-kit, achieving seamless UX with automatic server reconciliation on failure
- Wrote unit and integration tests (pytest + FastAPI TestClient) covering auth flows, project membership rules, and task movement logic across columns
- Containerized the full stack (backend, PostgreSQL, Next.js frontend) with Docker Compose, enabling one-command local development setup for new contributors
