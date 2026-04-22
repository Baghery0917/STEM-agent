# 数据库 Schema

## alembic_version

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| version_num | VARCHAR(32) | 否 |  |

**主键**: version_num

## chapters

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('chapters_id_seq'::regclass) |
| volume_id | INTEGER | 否 |  |
| title | VARCHAR(255) | 否 |  |
| description | TEXT | 是 |  |
| order | INTEGER | 否 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: volume_id → volumes.id

## llm_call_logs

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | BIGINT | 否 | nextval('llm_call_logs_id_seq'::regclass) |
| call_type | VARCHAR(6) | 否 |  |
| model | VARCHAR(128) | 否 |  |
| base_url | VARCHAR(512) | 否 |  |
| request_payload | JSONB | 否 |  |
| request_params | JSONB | 否 |  |
| response_text | TEXT | 是 |  |
| response_meta | JSONB | 是 |  |
| status | VARCHAR(7) | 否 |  |
| error | TEXT | 是 |  |
| duration_ms | INTEGER | 否 |  |
| teaching_session_id | INTEGER | 是 |  |
| student_id | INTEGER | 是 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: student_id → students.id
**外键**: teaching_session_id → teaching_sessions.id
**索引**: ix_llm_call_logs_call_type_created_at (call_type, created_at)
**索引**: ix_llm_call_logs_status_created_at (status, created_at)
**索引**: ix_llm_call_logs_student_id (student_id)
**索引**: ix_llm_call_logs_teaching_session_id (teaching_session_id)

## practice_items

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('practice_items_id_seq'::regclass) |
| student_id | INTEGER | 否 |  |
| practice_session_id | INTEGER | 否 |  |
| question_id | INTEGER | 否 |  |
| is_correct | BOOLEAN | 否 |  |
| is_skipped | BOOLEAN | 否 |  |
| started_at | TIMESTAMP | 否 |  |
| ended_at | TIMESTAMP | 是 |  |
| user_answer | TEXT | 否 |  |
| sequence | INTEGER | 否 |  |
| emotion | VARCHAR(50) | 是 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: practice_session_id → practice_sessions.id
**外键**: question_id → questions.id
**外键**: student_id → students.id
**索引**: UNIQUE uq_practice_session_question (practice_session_id, question_id)
**索引**: UNIQUE uq_practice_session_sequence (practice_session_id, sequence)

## practice_sessions

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('practice_sessions_id_seq'::regclass) |
| mode | VARCHAR(7) | 否 |  |
| knowledge_point_ids | ARRAY | 否 |  |
| difficulty_range | ARRAY | 否 |  |
| started_at | TIMESTAMP | 否 |  |
| ended_at | TIMESTAMP | 是 |  |
| student_id | INTEGER | 否 |  |
| skip_count | INTEGER | 否 |  |
| correct_count | INTEGER | 否 |  |
| wrong_count | INTEGER | 否 |  |
| total_count | INTEGER | 否 |  |
| skipped_question_ids | ARRAY | 否 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: student_id → students.id

## question_knowledge_points

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| question_id | INTEGER | 否 |  |
| section_id | INTEGER | 否 |  |

**主键**: question_id, section_id
**外键**: question_id → questions.id
**外键**: section_id → sections.id

## questions

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('questions_id_seq'::regclass) |
| type | VARCHAR(15) | 否 |  |
| content | TEXT | 否 |  |
| content_image | VARCHAR(500) | 是 |  |
| answer | TEXT | 否 |  |
| answer_image | VARCHAR(500) | 是 |  |
| analysis | TEXT | 是 |  |
| analysis_image | VARCHAR(500) | 是 |  |
| embedding | vector | 是 |  |
| difficulty | VARCHAR(6) | 否 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**索引**: ix_questions_difficulty (difficulty)
**索引**: ix_questions_type (type)

## sections

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('sections_id_seq'::regclass) |
| chapter_id | INTEGER | 否 |  |
| title | VARCHAR(255) | 否 |  |
| content | TEXT | 是 |  |
| order | INTEGER | 否 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: chapter_id → chapters.id

## student_knowledge_summaries

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('student_knowledge_summaries_id_seq'::regclass) |
| student_id | INTEGER | 否 |  |
| section_id | INTEGER | 否 |  |
| mastery_level | DOUBLE PRECISION | 否 |  |
| correct_count | INTEGER | 否 |  |
| total_practice_count | INTEGER | 否 |  |
| total_teaching_count | INTEGER | 否 |  |
| last_practice_at | TIMESTAMP | 是 |  |
| last_teaching_at | TIMESTAMP | 是 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: section_id → sections.id
**外键**: student_id → students.id
**索引**: UNIQUE uq_student_section (student_id, section_id)

## students

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('students_id_seq'::regclass) |
| name | VARCHAR(100) | 否 |  |
| gender | VARCHAR(6) | 否 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id

## teaching_messages

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('teaching_messages_id_seq'::regclass) |
| session_id | INTEGER | 否 |  |
| role | VARCHAR(9) | 否 |  |
| content | TEXT | 否 |  |
| message_type | VARCHAR(16) | 否 |  |
| sequence | INTEGER | 否 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: session_id → teaching_sessions.id
**索引**: UNIQUE uq_session_sequence (session_id, sequence)

## teaching_references

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('teaching_references_id_seq'::regclass) |
| message_id | INTEGER | 否 |  |
| question_id | INTEGER | 否 |  |
| similarity_score | DOUBLE PRECISION | 是 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
**外键**: message_id → teaching_messages.id
**外键**: question_id → questions.id

## teaching_sessions

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('teaching_sessions_id_seq'::regclass) |
| student_id | INTEGER | 否 |  |
| status | VARCHAR(9) | 否 |  |
| strategy | TEXT | 是 |  |
| ended_at | TIMESTAMP | 是 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |
| pipeline_status | VARCHAR(7) | 否 |  |

**主键**: id
**外键**: student_id → students.id

## volumes

| 列名 | 类型 | 可空 | 默认值 |
|------|------|------|--------|
| id | INTEGER | 否 | nextval('volumes_id_seq'::regclass) |
| title | VARCHAR(255) | 否 |  |
| description | TEXT | 是 |  |
| order | INTEGER | 否 |  |
| created_at | TIMESTAMP | 否 | now() |
| updated_at | TIMESTAMP | 否 | now() |

**主键**: id
