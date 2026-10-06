"""add emotion tables, message emotion columns, session end_reason

Revision ID: c1d2e3f4a5b6
Revises: a3e8331c5598
Create Date: 2026-10-06 18:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a3e8331c5598'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    end_reason_enum = sa.Enum('USER', 'IDLE', name='sessionendreason')
    end_reason_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'teaching_sessions',
        sa.Column('end_reason', end_reason_enum, nullable=True),
    )

    op.add_column('teaching_messages', sa.Column('facial_value', sa.Float(), nullable=True))
    op.add_column('teaching_messages', sa.Column('text_value', sa.Float(), nullable=True))
    op.add_column('teaching_messages', sa.Column('emotion_value', sa.Float(), nullable=True))

    op.create_table(
        'student_kp_emotions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('emotion_value', sa.Float(), nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('student_id', 'section_id', name='uq_student_kp_emotion'),
    )

    emotion_mode_enum = sa.Enum('TEACHING', 'PRACTICE', name='emotionmode')
    emotion_mode_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'emotion_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mode', emotion_mode_enum, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('emotion_value', sa.Float(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_emotion_logs_student_section', 'emotion_logs', ['student_id', 'section_id'])


def downgrade() -> None:
    op.drop_index('ix_emotion_logs_student_section', table_name='emotion_logs')
    op.drop_table('emotion_logs')
    sa.Enum(name='emotionmode').drop(op.get_bind(), checkfirst=True)
    op.drop_table('student_kp_emotions')
    op.drop_column('teaching_messages', 'emotion_value')
    op.drop_column('teaching_messages', 'text_value')
    op.drop_column('teaching_messages', 'facial_value')
    op.drop_column('teaching_sessions', 'end_reason')
    sa.Enum(name='sessionendreason').drop(op.get_bind(), checkfirst=True)
