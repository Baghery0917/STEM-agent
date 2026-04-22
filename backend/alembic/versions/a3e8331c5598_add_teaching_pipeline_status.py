"""add teaching pipeline_status

Revision ID: a3e8331c5598
Revises: ca4b5ef851cd
Create Date: 2026-04-22 19:04:38.855629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3e8331c5598'
down_revision: Union[str, None] = 'ca4b5ef851cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pipeline_status_enum = sa.Enum(
        'PENDING', 'RUNNING', 'DONE', 'FAILED', name='pipelinestatus',
    )
    pipeline_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'teaching_sessions',
        sa.Column(
            'pipeline_status',
            pipeline_status_enum,
            nullable=False,
            server_default='DONE',
        ),
    )
    op.alter_column('teaching_sessions', 'pipeline_status', server_default=None)


def downgrade() -> None:
    op.drop_column('teaching_sessions', 'pipeline_status')
    sa.Enum(name='pipelinestatus').drop(op.get_bind(), checkfirst=False)
