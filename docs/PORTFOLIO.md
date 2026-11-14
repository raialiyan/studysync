# StudySync — Portfolio and CV write-up

## One-line summary

StudySync is a full-stack, real-time collaboration platform for student teams, with task management, JWT-secured workspaces, PostgreSQL persistence and live WebSocket updates.

## Portfolio case study

### Problem

Student teams commonly coordinate coursework across separate messages, checklists and files. Keeping track of ownership, changing priorities and current task status can become fragmented.

### Solution

I built StudySync, a shared workspace application that groups coursework into modules and enables members to create, assign, discuss and update tasks. Live WebSocket events keep multiple connected users informed of changes without manual refreshing.

### My engineering approach

The frontend uses React/Vite, while a FastAPI backend enforces JWT authentication and workspace permissions. SQLAlchemy and PostgreSQL persist tasks, comments and activity. I containerised the application for local integration testing, used Alembic for schema management and deployed the frontend, API and database separately across Vercel, Render and Supabase.

### Verification

I validated 14 backend integration checks, 17 Docker end-to-end checks and 18 cloud production checks. The production suite covered access control, persistence and WebSocket notification delivery to two authenticated clients.

### What I learned

Building a collaborative application required more than creating components and routes: I had to design role-aware access control, synchronise persisted state with real-time events, isolate local and cloud environments and debug production deployment issues such as database credentials, React routing and CORS.

## CV bullets (choose 2–3)

**StudySync — Full-Stack Collaborative Task Management Platform** | React, TypeScript? **No — JavaScript**, FastAPI, PostgreSQL, WebSockets, Docker, Vercel, Render

- Developed and deployed a full-stack collaborative study platform using **React, FastAPI and PostgreSQL**, supporting shared workspaces, modules, task assignments, comments and activity history.
- Implemented **JWT authentication, role-based workspace permissions and WebSocket updates** to support secure, real-time task collaboration between connected users.
- Containerised the stack with **Docker Compose**, introduced database migrations and validated functionality with **14 backend, 17 Docker and 18 production automated checks**.

> Do not add features, performance improvements or user counts that you have not measured. The app currently uses JavaScript, not TypeScript.

## Interview talking points

- How JWTs and membership checks protect private workspace data.
- Why persisted PostgreSQL state and in-memory WebSocket events need separate handling.
- How WebSocket updates and API re-fetching keep multiple browser sessions consistent.
- How Docker Compose reduces differences between development and deployment environments.
- How you debugged CORS origin mismatches and cloud database connection failures.
- How you would scale WebSocket broadcasts with Redis/pub-sub and add observability.
