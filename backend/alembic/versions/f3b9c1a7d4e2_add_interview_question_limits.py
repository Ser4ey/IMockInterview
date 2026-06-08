"""Add interview question limits

Revision ID: f3b9c1a7d4e2
Revises: d7c6f7a91a20
Create Date: 2026-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3b9c1a7d4e2"
down_revision: Union[str, None] = "d7c6f7a91a20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("interview_types") as batch_op:
        batch_op.add_column(sa.Column("default_question_count", sa.Integer(), nullable=False, server_default="3"))

    with op.batch_alter_table("interview_sessions") as batch_op:
        batch_op.add_column(sa.Column("question_limit", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("interview_sessions") as batch_op:
        batch_op.drop_column("question_limit")

    with op.batch_alter_table("interview_types") as batch_op:
        batch_op.drop_column("default_question_count")
