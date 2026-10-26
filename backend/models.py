
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ==========================================
# USER
# ==========================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee"
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author"
    )


# ==========================================
# WORKSPACE
# ==========================================

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan"
    )

    # A workspace can contain multiple modules
    modules: Mapped[list["Module"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan"
    )


# ==========================================
# MEMBERSHIP
# ==========================================

class Membership(Base):
    __tablename__ = "memberships"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "workspace_id",
            name="uq_user_workspace"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="member",
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="memberships"
    )

    workspace: Mapped["Workspace"] = relationship(
        back_populates="memberships"
    )


# ==========================================
# MODULE
# ==========================================

class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(
        back_populates="modules"
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan"
    )


# ==========================================
# TASK
# ==========================================

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="todo",
        nullable=False
    )

    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id"),
        nullable=False
    )

    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    module: Mapped["Module"] = relationship(
        back_populates="tasks"
    )

    assignee: Mapped["User | None"] = relationship(
        back_populates="assigned_tasks"
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )


# ==========================================
# COMMENT
# ==========================================

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    content: Mapped[str] = mapped_column(
        String(2000),
        nullable=False
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    task: Mapped["Task"] = relationship(
        back_populates="comments"
    )

    author: Mapped["User"] = relationship(
        back_populates="comments"
    )
