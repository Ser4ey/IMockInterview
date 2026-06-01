"""Add question bank

Revision ID: a2f4c2d91e13
Revises: c01b8c94313c
Create Date: 2026-05-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2f4c2d91e13"
down_revision: Union[str, None] = "c01b8c94313c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("technology_stack", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("levels", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_types_id"), "interview_types", ["id"], unique=False)
    op.create_index(op.f("ix_interview_types_title"), "interview_types", ["title"], unique=True)
    op.create_index(op.f("ix_interview_types_role"), "interview_types", ["role"], unique=False)

    op.create_table(
        "question_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_sources_id"), "question_sources", ["id"], unique=False)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interview_type_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("evaluation_criteria", sa.Text(), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.ForeignKeyConstraint(["interview_type_id"], ["interview_types.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["question_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_id"), "questions", ["id"], unique=False)
    op.create_index(op.f("ix_questions_interview_type_id"), "questions", ["interview_type_id"], unique=False)
    op.create_index(op.f("ix_questions_level"), "questions", ["level"], unique=False)

    op.create_table(
        "question_generation_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interview_type_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("generated_count", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["interview_type_id"], ["interview_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_generation_jobs_id"), "question_generation_jobs", ["id"], unique=False)
    op.create_index(
        op.f("ix_question_generation_jobs_interview_type_id"),
        "question_generation_jobs",
        ["interview_type_id"],
        unique=False,
    )
    op.create_index(op.f("ix_question_generation_jobs_level"), "question_generation_jobs", ["level"], unique=False)

    with op.batch_alter_table("interview_sessions") as batch_op:
        batch_op.add_column(sa.Column("interview_type_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("current_question_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("question_index", sa.Integer(), nullable=False, server_default="0"))
        batch_op.create_index("ix_interview_sessions_interview_type_id", ["interview_type_id"])

    with op.batch_alter_table("interview_messages") as batch_op:
        batch_op.add_column(sa.Column("question_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_interview_messages_question_id", ["question_id"])

    with op.batch_alter_table("interview_results") as batch_op:
        batch_op.add_column(sa.Column("strengths", sa.Text(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("weaknesses", sa.Text(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("summary", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("interview_results") as batch_op:
        batch_op.drop_column("summary")
        batch_op.drop_column("weaknesses")
        batch_op.drop_column("strengths")
    with op.batch_alter_table("interview_messages") as batch_op:
        batch_op.drop_index("ix_interview_messages_question_id")
        batch_op.drop_column("question_id")
    with op.batch_alter_table("interview_sessions") as batch_op:
        batch_op.drop_index("ix_interview_sessions_interview_type_id")
        batch_op.drop_column("question_index")
        batch_op.drop_column("current_question_id")
        batch_op.drop_column("interview_type_id")
    op.drop_table("question_generation_jobs")
    op.drop_table("questions")
    op.drop_table("question_sources")
    op.drop_table("interview_types")
