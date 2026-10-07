# StudySync Architecture

## MVP

StudySync will allow users to:

- Register and log in
- Create workspaces
- Add members to workspaces
- Use Owner and Member roles
- Create modules inside workspaces
- Create, update, delete and assign tasks
- Comment on tasks
- View workspace activity
- Receive real-time task and comment updates
- Use a clean dashboard

## Architecture

Frontend:
React + Vite

Backend:
FastAPI

Database:
PostgreSQL

ORM:
SQLAlchemy

Authentication:
JWT + password hashing

Real-time:
WebSockets

Testing:
Pytest

Deployment:
Docker + cloud hosting

## Request Flow

React frontend
↓
FastAPI REST API
↓
SQLAlchemy
↓
PostgreSQL

For real-time events:

FastAPI WebSocket
↓
Connected React clients

## Core Entities

- User
- Workspace
- Membership
- Module
- Task
- Comment

## Scope Guard

Do not add the following until the MVP is complete:

- AI features
- File uploads
- Video/chat
- Rich-text editors
- Redis
- Microservices
- Advanced analytics