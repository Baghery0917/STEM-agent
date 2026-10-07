"""student persona and teaching session persona snapshot

Revision ID: e1f2a3b4c5d6
Revises: d2e3f4a5b6c7
Create Date: 2026-10-07 20:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PERSONA = sa.Enum(
    'leonard', 'penny', 'howard', 'raj', 'bernadette', 'amy', 'sheldon', name='persona',
)


def upgrade() -> None:
    _PERSONA.create(op.get_bind(), checkfirst=True)
    op.add_column('students', sa.Column('persona', _PERSONA, nullable=True))
    op.add_column('teaching_sessions', sa.Column('persona', _PERSONA, nullable=True))


def downgrade() -> None:
    op.drop_column('teaching_sessions', 'persona')
    op.drop_column('students', 'persona')
    _PERSONA.drop(op.get_bind(), checkfirst=True)
