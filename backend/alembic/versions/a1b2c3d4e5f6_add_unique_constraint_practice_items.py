"""add unique constraint on practice_items (session_id, question_id)

Revision ID: a1b2c3d4e5f6
Revises: fe4da053e0b3
Create Date: 2026-04-22 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fe4da053e0b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_practice_session_question',
        'practice_items',
        ['practice_session_id', 'question_id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_practice_session_question',
        'practice_items',
        type_='unique',
    )
