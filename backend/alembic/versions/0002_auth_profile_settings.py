"""add auth, profile edit, and app settings fields

Revision ID: 0002_auth_profile_settings
Revises: 0001_init_postgres_schema
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_auth_profile_settings"
down_revision = "0001_init_postgres_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("workout_intro", sa.Text(), nullable=True))
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column("user_settings", sa.Column("auto_play_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("user_settings", sa.Column("muted_by_default", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("user_settings", sa.Column("save_original_video", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("user_settings", sa.Column("show_ai_feedback", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("user_settings", sa.Column("post_after_analysis", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("user_settings", "post_after_analysis")
    op.drop_column("user_settings", "show_ai_feedback")
    op.drop_column("user_settings", "save_original_video")
    op.drop_column("user_settings", "muted_by_default")
    op.drop_column("user_settings", "auto_play_enabled")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "workout_intro")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
