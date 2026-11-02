"""StudySync Week 3: task CRUD, assignment, comments, and persistent activity."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from auth import get_current_user
from database import Base, get_db
from models import Comment, Membership, Module, Task, User

router = APIRouter(tags=["Week 3: tasks and collaboration"])
TaskStatus = Literal["todo", "in_progress", "done"]


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    status: TaskStatus = "todo"
    assigned_to_id: int | None = Field(default=None, gt=0)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    status: TaskStatus | None = None
    assigned_to_id: int | None = Field(default=None, gt=0)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    module_id: int
    assigned_to_id: int | None
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: int
    content: str
    task_id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class ActivityResponse(BaseModel):
    id: int
    workspace_id: int
    actor_user_id: int | None
    event_type: str
    entity_type: str
    entity_id: int
    details: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def require_membership(db: Session, workspace_id: int, user_id: int):
    membership = db.scalar(select(Membership).where(Membership.workspace_id == workspace_id, Membership.user_id == user_id))
    if membership is None:
        raise HTTPException(404, "Workspace not found")
    return membership


def visible_module(db: Session, module_id: int, user_id: int) -> Module:
    module = db.get(Module, module_id)
    if module is None:
        raise HTTPException(404, "Module not found")
    require_membership(db, module.workspace_id, user_id)
    return module


def visible_task(db: Session, task_id: int, user_id: int) -> tuple[Task, Module]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task, visible_module(db, task.module_id, user_id)


def valid_assignee(db: Session, workspace_id: int, assignee_id: int | None):
    if assignee_id is None:
        return
    if not db.scalar(select(Membership.id).where(Membership.workspace_id == workspace_id, Membership.user_id == assignee_id)):
        raise HTTPException(422, "Assignee must belong to the workspace")


def record_event(db: Session, workspace_id: int, actor_id: int, event: str, entity_type: str, entity_id: int, details: dict | None = None):
    db.add(Activity(workspace_id=workspace_id, actor_user_id=actor_id, event_type=event, entity_type=entity_type, entity_id=entity_id, details=details or {}))


@router.post("/modules/{module_id}/tasks", response_model=TaskResponse, status_code=201)
def create_task(module_id: int, data: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = visible_module(db, module_id, user.id)
    title = data.title.strip()
    if not title:
        raise HTTPException(422, "Task title cannot be blank")
    valid_assignee(db, module.workspace_id, data.assigned_to_id)
    task = Task(module_id=module_id, title=title, description=data.description, status=data.status, assigned_to_id=data.assigned_to_id)
    db.add(task)
    db.flush()
    record_event(db, module.workspace_id, user.id, "task_created", "task", task.id, {"title": title})
    if data.assigned_to_id is not None:
        record_event(db, module.workspace_id, user.id, "task_assigned", "task", task.id, {"assigned_to_id": data.assigned_to_id})
    db.commit()
    db.refresh(task)
    return task


@router.get("/modules/{module_id}/tasks", response_model=list[TaskResponse])
def list_tasks(module_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    visible_module(db, module_id, user.id)
    return db.scalars(select(Task).where(Task.module_id == module_id).order_by(Task.id)).all()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task, _ = visible_task(db, task_id, user.id)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task, module = visible_task(db, task_id, user.id)
    changes = data.model_dump(exclude_unset=True)
    if "title" in changes:
        if changes["title"] is None or not changes["title"].strip():
            raise HTTPException(422, "Task title cannot be blank")
        changes["title"] = changes["title"].strip()
    if "status" in changes and changes["status"] is None:
        raise HTTPException(422, "Task status cannot be null")
    if "assigned_to_id" in changes:
        valid_assignee(db, module.workspace_id, changes["assigned_to_id"])
    for field, value in changes.items():
        old_value = getattr(task, field)
        if old_value == value:
            continue
        setattr(task, field, value)
        if field == "status":
            record_event(db, module.workspace_id, user.id, "task_status_changed", "task", task.id, {"from": old_value, "to": value})
        elif field == "assigned_to_id":
            record_event(db, module.workspace_id, user.id, "task_assigned", "task", task.id, {"from": old_value, "to": value})
        else:
            record_event(db, module.workspace_id, user.id, "task_updated", "task", task.id, {"field": field})
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task, module = visible_task(db, task_id, user.id)
    record_event(db, module.workspace_id, user.id, "task_deleted", "task", task.id, {"title": task.title})
    db.delete(task)
    db.commit()


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(task_id: int, data: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _, module = visible_task(db, task_id, user.id)
    content = data.content.strip()
    if not content:
        raise HTTPException(422, "Comment cannot be blank")
    comment = Comment(task_id=task_id, user_id=user.id, content=content)
    db.add(comment)
    db.flush()
    record_event(db, module.workspace_id, user.id, "comment_added", "comment", comment.id, {"task_id": task_id})
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/tasks/{task_id}/comments", response_model=list[CommentResponse])
def list_comments(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    visible_task(db, task_id, user.id)
    return db.scalars(select(Comment).where(Comment.task_id == task_id).order_by(Comment.id)).all()


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(404, "Comment not found")
    _, module = visible_task(db, comment.task_id, user.id)
    if comment.user_id != user.id:
        raise HTTPException(403, "Only the comment author can delete this comment")
    record_event(db, module.workspace_id, user.id, "comment_deleted", "comment", comment.id, {"task_id": comment.task_id})
    db.delete(comment)
    db.commit()


@router.get("/workspaces/{workspace_id}/activity", response_model=list[ActivityResponse])
def get_activity(workspace_id: int, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_membership(db, workspace_id, user.id)
    if not 1 <= limit <= 100:
        raise HTTPException(422, "limit must be between 1 and 100")
    return db.scalars(select(Activity).where(Activity.workspace_id == workspace_id).order_by(Activity.id.desc()).limit(limit)).all()
