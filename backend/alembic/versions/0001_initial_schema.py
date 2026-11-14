"""Initial StudySync schema baseline for FRESH databases only.

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Explicit baseline schema. Existing databases must be validated then STAMPED,
    # not upgraded from zero; never recreate tables over existing user data.
    op.create_table("users", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("email", sa.String(255), nullable=False, unique=True),
                    sa.Column("hashed_password", sa.String(255), nullable=False))
    op.create_table("workspaces", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("name", sa.String(255), nullable=False))
    op.create_table("memberships", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
                    sa.Column("workspace_id", sa.Integer, sa.ForeignKey("workspaces.id"), nullable=False),
                    sa.Column("role", sa.String(20), nullable=False),
                    sa.UniqueConstraint("user_id", "workspace_id", name="uq_user_workspace"))
    op.create_table("modules", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("name", sa.String(255), nullable=False),
                    sa.Column("workspace_id", sa.Integer, sa.ForeignKey("workspaces.id"), nullable=False))
    op.create_table("tasks", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("title", sa.String(255), nullable=False),
                    sa.Column("description", sa.String(1000)),
                    sa.Column("status", sa.String(20), nullable=False),
                    sa.Column("module_id", sa.Integer, sa.ForeignKey("modules.id"), nullable=False),
                    sa.Column("assigned_to_id", sa.Integer, sa.ForeignKey("users.id")))
    op.create_table("comments", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("content", sa.String(2000), nullable=False),
                    sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=False),
                    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False))
    op.create_table("activities", sa.Column("id", sa.Integer, primary_key=True),
                    sa.Column("workspace_id", sa.Integer, sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("actor_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
                    sa.Column("event_type", sa.String(60), nullable=False),
                    sa.Column("entity_type", sa.String(40), nullable=False),
                    sa.Column("entity_id", sa.Integer, nullable=False),
                    sa.Column("details", sa.JSON, nullable=False),
                    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_activities_workspace_id", "activities", ["workspace_id"])


def downgrade():
    raise RuntimeError("Destructive downgrade disabled for safety. Restore from backup if needed.")
