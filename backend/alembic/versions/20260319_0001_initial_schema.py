"""initial schema

Revision ID: 20260319_0001
Revises:
Create Date: 2026-03-19 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260319_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("student_number", sa.String(length=32), nullable=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(student_number IS NOT NULL AND last_name IS NOT NULL) OR username IS NOT NULL",
            name="users_login_identity_check",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_number"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.SmallInteger(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "token_periods",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("end_date >= start_date", name="token_periods_date_check"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_token_balances",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_period_id", sa.BigInteger(), nullable=False),
        sa.Column("lunches_remaining", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("suppers_remaining", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("lunches_remaining >= 0 AND suppers_remaining >= 0", name="token_balance_nonnegative"),
        sa.ForeignKeyConstraint(["token_period_id"], ["token_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "token_period_id", name="uq_user_token_balance"),
    )

    op.create_table(
        "meal_days",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_date"),
    )

    op.create_table(
        "meals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("meal_day_id", sa.BigInteger(), nullable=False),
        sa.Column("meal_type", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("is_signup_allowed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("meal_type IN ('Breakfast', 'Lunch', 'Supper', 'Snack')", name="meals_type_check"),
        sa.ForeignKeyConstraint(["meal_day_id"], ["meal_days.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meal_day_id", "meal_type", name="uq_meal_day_type"),
    )

    op.create_table(
        "meal_signups",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("meal_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("signed_up_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.CheckConstraint("status IN ('active', 'cancelled')", name="meal_signups_status_check"),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meal_id", "user_id", name="uq_meal_signup"),
    )

    op.create_table(
        "menu_uploads",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("parsed_success", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "password_change_audit",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("changed_by", sa.BigInteger(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_meal_days_service_date", "meal_days", ["service_date"], unique=False)
    op.create_index("idx_meals_day_type", "meals", ["meal_day_id", "meal_type"], unique=False)
    op.create_index("idx_signups_meal", "meal_signups", ["meal_id"], unique=False)
    op.create_index("idx_signups_user", "meal_signups", ["user_id"], unique=False)

    op.execute("INSERT INTO roles(name) VALUES ('Student'), ('Apartment Resident'), ('Staff'), ('Admin')")

    admin_hash = "$2b$12$tF90DUizTMgF3Rlk.wl2N.8/6CWxP4TjkJrMq0FdMMtdfFvOm6N2K"
    student_hash = "$2b$12$N2eEYhN8fCC/eV4UrJjHhuy4u9ww69bgDPPQjKJfLMmxYe56PmYdq"

    op.execute(
        sa.text("INSERT INTO users(username, password_hash) VALUES (:username, :password_hash) ON CONFLICT (username) DO NOTHING")
        .bindparams(username="admin", password_hash=admin_hash)
    )
    op.execute(
        sa.text(
            "INSERT INTO users(student_number, last_name, password_hash) VALUES (:student_number, :last_name, :password_hash) "
            "ON CONFLICT (student_number) DO NOTHING"
        ).bindparams(student_number="123", last_name="student", password_hash=student_hash)
    )

    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id
        FROM users u
        JOIN roles r ON r.name = 'Admin'
        WHERE u.username = 'admin'
        ON CONFLICT (user_id, role_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id
        FROM users u
        JOIN roles r ON r.name = 'Student'
        WHERE u.student_number = '123'
        ON CONFLICT (user_id, role_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("idx_signups_user", table_name="meal_signups")
    op.drop_index("idx_signups_meal", table_name="meal_signups")
    op.drop_index("idx_meals_day_type", table_name="meals")
    op.drop_index("idx_meal_days_service_date", table_name="meal_days")
    op.drop_table("password_change_audit")
    op.drop_table("menu_uploads")
    op.drop_table("meal_signups")
    op.drop_table("meals")
    op.drop_table("meal_days")
    op.drop_table("user_token_balances")
    op.drop_table("token_periods")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
