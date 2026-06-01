"""Add question generation diagnostics

Revision ID: d7c6f7a91a20
Revises: a2f4c2d91e13
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7c6f7a91a20"
down_revision: Union[str, None] = "a2f4c2d91e13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.add_column(sa.Column("question_hash", sa.String(), nullable=True))
        batch_op.create_index("ix_questions_question_hash", ["question_hash"], unique=False)

    with op.batch_alter_table("question_generation_jobs") as batch_op:
        batch_op.add_column(sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("provider", sa.String(), nullable=False, server_default="mock"))
        batch_op.add_column(sa.Column("context_used", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("raw_response_preview", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("question_generation_jobs") as batch_op:
        batch_op.drop_column("raw_response_preview")
        batch_op.drop_column("context_used")
        batch_op.drop_column("provider")
        batch_op.drop_column("skipped_count")

    with op.batch_alter_table("questions") as batch_op:
        batch_op.drop_index("ix_questions_question_hash")
        batch_op.drop_column("question_hash")
