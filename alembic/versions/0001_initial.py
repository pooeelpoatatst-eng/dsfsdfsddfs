"""Initial hosted userbot schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

JSON = postgresql.JSONB(astext_type=sa.Text())

def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("control_bot_user_id", sa.BigInteger(), nullable=False, unique=True), sa.Column("telegram_account_id", sa.BigInteger(), unique=True), sa.Column("username", sa.String(255)), sa.Column("first_name", sa.String(255)), sa.Column("encrypted_session", sa.Text()), sa.Column("connected", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("plan", sa.String(32), nullable=False, server_default="free"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("last_seen", sa.DateTime(timezone=True)))
    op.create_index("ix_users_connected", "users", ["connected"]); op.create_index("ix_users_control_bot_user_id", "users", ["control_bot_user_id"])
    op.create_table("user_settings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("key", sa.String(100), nullable=False), sa.Column("value_json", JSON, nullable=False), sa.UniqueConstraint("user_id", "key", name="uq_user_settings_key"))
    op.create_table("chat_modes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("chat_id", sa.BigInteger(), nullable=False), sa.Column("mode", sa.String(64), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False), sa.Column("config_json", JSON, nullable=False), sa.UniqueConstraint("user_id", "chat_id", "mode", name="uq_chat_mode"))
    op.create_table("afk_states", sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("enabled", sa.Boolean(), nullable=False), sa.Column("since", sa.DateTime(timezone=True)), sa.Column("reason", sa.String(500)))
    op.create_table("notes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("chat_id", sa.BigInteger()), sa.Column("name", sa.String(100), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("user_id", "chat_id", "name", name="uq_note_name"))
    op.create_table("ai_usage", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("date", sa.Date(), nullable=False), sa.Column("requests", sa.Integer(), nullable=False), sa.Column("prompt_tokens", sa.Integer(), nullable=False), sa.Column("completion_tokens", sa.Integer(), nullable=False), sa.Column("total_tokens", sa.Integer(), nullable=False), sa.Column("errors", sa.Integer(), nullable=False), sa.UniqueConstraint("user_id", "date", name="uq_ai_usage_day"))
    op.create_table("command_usage", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("command", sa.String(64), nullable=False), sa.Column("count", sa.Integer(), nullable=False), sa.Column("last_used", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("user_id", "command", name="uq_command_usage"))
    op.create_table("game_sessions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("chat_id", sa.BigInteger(), nullable=False), sa.Column("game_type", sa.String(32), nullable=False), sa.Column("state_json", JSON, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("login_audit", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("control_bot_user_id", sa.BigInteger(), nullable=False), sa.Column("event", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))

def downgrade() -> None:
    for table in ("login_audit", "game_sessions", "command_usage", "ai_usage", "notes", "afk_states", "chat_modes", "user_settings", "users"): op.drop_table(table)
