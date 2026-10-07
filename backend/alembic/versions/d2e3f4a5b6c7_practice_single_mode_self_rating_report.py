"""practice single mode (timed flag, pre-drawn questions, star), teaching self-rating & practice handoff, student explain style

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-10-07 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- practice_sessions: 专项/综合 -> 计时/不计时，一次抽满题目，星标 ---
    op.add_column(
        'practice_sessions',
        sa.Column('timed', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'practice_sessions',
        sa.Column('instant_feedback', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.add_column(
        'practice_sessions',
        sa.Column('question_ids', postgresql.ARRAY(sa.Integer()), nullable=False, server_default='{}'),
    )
    op.add_column(
        'practice_sessions',
        sa.Column('starred_question_ids', postgresql.ARRAY(sa.Integer()), nullable=False, server_default='{}'),
    )
    # 历史会话：把已作答题目回填为 question_ids，保证回顾页能列出题目
    op.execute(
        """
        UPDATE practice_sessions ps
        SET question_ids = COALESCE(
            (SELECT ARRAY_AGG(pi.question_id ORDER BY pi.sequence)
             FROM practice_items pi WHERE pi.practice_session_id = ps.id),
            '{}'
        )
        """
    )
    op.drop_column('practice_sessions', 'skipped_question_ids')
    op.drop_column('practice_sessions', 'mode')
    op.execute('DROP TYPE IF EXISTS practicemode')

    # --- practice_items: 用时与面部情绪数值 ---
    op.add_column('practice_items', sa.Column('duration_seconds', sa.Integer(), nullable=True))
    op.add_column('practice_items', sa.Column('emotion_value', sa.Float(), nullable=True))

    # --- teaching: 自评 + 练习转教学来源 ---
    op.add_column('teaching_messages', sa.Column('self_rating', sa.Integer(), nullable=True))
    op.add_column(
        'teaching_sessions',
        sa.Column(
            'source_practice_session_id', sa.Integer(),
            sa.ForeignKey('practice_sessions.id', ondelete='SET NULL'), nullable=True,
        ),
    )
    op.add_column(
        'teaching_sessions',
        sa.Column('source_question_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
    )

    # --- students: 讲解风格覆盖 ---
    explain_style = sa.Enum('DIRECT', 'GUIDED', 'HINT', name='explainstyle')
    explain_style.create(op.get_bind(), checkfirst=True)
    op.add_column('students', sa.Column('explain_style', explain_style, nullable=True))


def downgrade() -> None:
    op.drop_column('students', 'explain_style')
    sa.Enum(name='explainstyle').drop(op.get_bind(), checkfirst=True)

    op.drop_column('teaching_sessions', 'source_question_ids')
    op.drop_column('teaching_sessions', 'source_practice_session_id')
    op.drop_column('teaching_messages', 'self_rating')

    op.drop_column('practice_items', 'emotion_value')
    op.drop_column('practice_items', 'duration_seconds')

    op.execute("CREATE TYPE practicemode AS ENUM ('FOCUSED', 'GENERAL')")
    op.add_column(
        'practice_sessions',
        sa.Column('mode', sa.Enum('FOCUSED', 'GENERAL', name='practicemode', create_type=False),
                  nullable=False, server_default='FOCUSED'),
    )
    op.add_column(
        'practice_sessions',
        sa.Column('skipped_question_ids', postgresql.ARRAY(sa.Integer()), nullable=False, server_default='{}'),
    )
    op.drop_column('practice_sessions', 'starred_question_ids')
    op.drop_column('practice_sessions', 'question_ids')
    op.drop_column('practice_sessions', 'instant_feedback')
    op.drop_column('practice_sessions', 'timed')
