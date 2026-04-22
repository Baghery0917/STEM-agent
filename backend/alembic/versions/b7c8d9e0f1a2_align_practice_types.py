"""align practice_sessions types with model

- mode: VARCHAR(20) -> practicemode ENUM
- difficulty_range: VARCHAR[] -> difficulty[] ENUM
- started_at / ended_at: timestamp -> timestamptz
- practice_items.started_at / ended_at: timestamp -> timestamptz

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-04-22 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE practicemode AS ENUM ('FOCUSED', 'GENERAL')"
    )

    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN mode TYPE practicemode "
        "USING (UPPER(mode)::practicemode)"
    )

    # PostgreSQL 禁止在 ALTER COLUMN USING 里直接用子查询/UNNEST，
    # 这里用 IMMUTABLE 辅助函数把 varchar[] 转成 difficulty[]。
    op.execute(
        """
        CREATE OR REPLACE FUNCTION _varchar_to_difficulty_array(arr VARCHAR[])
        RETURNS difficulty[] AS $$
            SELECT COALESCE(
                ARRAY_AGG(UPPER(x)::difficulty),
                ARRAY[]::difficulty[]
            )
            FROM UNNEST(arr) AS x;
        $$ LANGUAGE SQL IMMUTABLE;
        """
    )
    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN difficulty_range TYPE difficulty[] "
        "USING _varchar_to_difficulty_array(difficulty_range)"
    )
    op.execute("DROP FUNCTION _varchar_to_difficulty_array(VARCHAR[])")

    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN started_at TYPE TIMESTAMPTZ USING started_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN ended_at TYPE TIMESTAMPTZ USING ended_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_items "
        "ALTER COLUMN started_at TYPE TIMESTAMPTZ USING started_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_items "
        "ALTER COLUMN ended_at TYPE TIMESTAMPTZ USING ended_at AT TIME ZONE 'UTC'"
    )

    # Align teaching_sessions.ended_at and student_knowledge_summaries.last_* to TIMESTAMPTZ
    op.execute(
        "ALTER TABLE teaching_sessions "
        "ALTER COLUMN ended_at TYPE TIMESTAMPTZ USING ended_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE student_knowledge_summaries "
        "ALTER COLUMN last_practice_at TYPE TIMESTAMPTZ USING last_practice_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE student_knowledge_summaries "
        "ALTER COLUMN last_teaching_at TYPE TIMESTAMPTZ USING last_teaching_at AT TIME ZONE 'UTC'"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE student_knowledge_summaries "
        "ALTER COLUMN last_teaching_at TYPE TIMESTAMP USING last_teaching_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE student_knowledge_summaries "
        "ALTER COLUMN last_practice_at TYPE TIMESTAMP USING last_practice_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE teaching_sessions "
        "ALTER COLUMN ended_at TYPE TIMESTAMP USING ended_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_items "
        "ALTER COLUMN ended_at TYPE TIMESTAMP USING ended_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_items "
        "ALTER COLUMN started_at TYPE TIMESTAMP USING started_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN ended_at TYPE TIMESTAMP USING ended_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN started_at TYPE TIMESTAMP USING started_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN difficulty_range TYPE VARCHAR(20)[] USING difficulty_range::varchar[]"
    )
    op.execute(
        "ALTER TABLE practice_sessions "
        "ALTER COLUMN mode TYPE VARCHAR(20) USING LOWER(mode::text)"
    )
    op.execute("DROP TYPE practicemode")
