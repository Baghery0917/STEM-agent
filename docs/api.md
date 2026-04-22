# STEM API 接口文档

Base URL: `http://localhost:8000/api/v1`

---

## Health

### GET /health
健康检查。

**Response:**
```json
{
  "status": "healthy"
}
```

### GET /health/db
数据库健康检查。

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Knowledge Structure（知识体系）

### Volume（册）

#### POST /volumes
创建册。

**Request Body:**
```json
{
  "title": "string (required, 1-255 chars)",
  "description": "string | null",
  "order": "integer, default 0, >= 0"
}
```

**Response (201):**
```json
{
  "id": 1,
  "title": "string",
  "description": "string | null",
  "order": 0,
  "created_at": "2026-04-22T12:00:00",
  "updated_at": "2026-04-22T12:00:00"
}
```

#### GET /volumes
获取册列表。

**Query Parameters:**
- `skip` (int, default 0)
- `limit` (int, default 100)

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "string",
    "description": "string | null",
    "order": 0,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

#### GET /volumes/{volume_id}
获取单个册。

**Response (200):** 同 VolumeResponse

**Error:** 404 - Volume not found

#### PUT /volumes/{volume_id}
更新册。

**Request Body:**
```json
{
  "title": "string | null (1-255 chars)",
  "description": "string | null",
  "order": "integer | null, >= 0"
}
```

**Response (200):** VolumeResponse

**Error:** 404 - Volume not found

#### DELETE /volumes/{volume_id}
删除册。

**Response (204):** No Content

**Error:** 404 - Volume not found

#### GET /volumes/{volume_id}/chapters
获取册下的所有章。

**Response (200):** `list[ChapterResponse]`

**Error:** 404 - Volume not found

---

### Chapter（章）

#### POST /chapters
创建章。

**Request Body:**
```json
{
  "volume_id": "integer (required)",
  "title": "string (required, 1-255 chars)",
  "description": "string | null",
  "order": "integer, default 0, >= 0"
}
```

**Response (201):** ChapterResponse

**Error:** 404 - Volume not found

#### GET /chapters
获取章列表。

**Query Parameters:**
- `skip` (int, default 0)
- `limit` (int, default 100)

**Response (200):** `list[ChapterResponse]`

#### GET /chapters/{chapter_id}
获取单个章。

**Response (200):** ChapterResponse

**Error:** 404 - Chapter not found

#### PUT /chapters/{chapter_id}
更新章。

**Request Body:**
```json
{
  "volume_id": "integer | null",
  "title": "string | null (1-255 chars)",
  "description": "string | null",
  "order": "integer | null, >= 0"
}
```

**Response (200):** ChapterResponse

**Error:** 404 - Volume not found / Chapter not found

#### DELETE /chapters/{chapter_id}
删除章。

**Response (204):** No Content

**Error:** 404 - Chapter not found

#### GET /chapters/{chapter_id}/sections
获取章下的所有节（知识点）。

**Response (200):** `list[SectionResponse]`

**Error:** 404 - Chapter not found

---

### Section（节 / 知识点）

#### POST /sections
创建节。

**Request Body:**
```json
{
  "chapter_id": "integer (required)",
  "title": "string (required, 1-255 chars)",
  "content": "string | null",
  "order": "integer, default 0, >= 0"
}
```

**Response (201):** SectionResponse

**Error:** 404 - Chapter not found

#### GET /sections
获取节列表。

**Query Parameters:**
- `skip` (int, default 0)
- `limit` (int, default 100)

**Response (200):** `list[SectionResponse]`

#### GET /sections/{section_id}
获取单个节。

**Response (200):** SectionResponse

**Error:** 404 - Section not found

#### PUT /sections/{section_id}
更新节。

**Request Body:**
```json
{
  "chapter_id": "integer | null",
  "title": "string | null (1-255 chars)",
  "content": "string | null",
  "order": "integer | null, >= 0"
}
```

**Response (200):** SectionResponse

**Error:** 404 - Chapter not found / Section not found

#### DELETE /sections/{section_id}
删除节。

**Response (204):** No Content

**Error:** 404 - Section not found

---

## Questions（题库）

#### POST /questions
创建题目。

**Request Body:**
```json
{
  "type": "enum: single_choice | multiple_choice | fill_blank | short_answer | calculation",
  "content": "string (required, min_length=1)",
  "content_image": "string | null",
  "answer": "string (required, min_length=1)",
  "answer_image": "string | null",
  "analysis": "string | null",
  "analysis_image": "string | null",
  "difficulty": "enum: easy | medium | hard (default: medium)",
  "knowledge_point_ids": "list[int] (default: [])"
}
```

**Response (201):** QuestionResponse

#### GET /questions
获取题目列表。

**Query Parameters:**
- `skip` (int, default 0)
- `limit` (int, default 20)
- `type` (enum: single_choice | multiple_choice | fill_blank | short_answer | calculation)
- `difficulty` (enum: easy | medium | hard)
- `knowledge_point_ids` (list[int], default [])
- `volume_id` (int)
- `chapter_id` (int)

**Response (200):**
```json
[
  {
    "id": 1,
    "type": "single_choice",
    "content": "string",
    "content_image": "string | null",
    "answer": "string",
    "answer_image": "string | null",
    "analysis": "string | null",
    "analysis_image": "string | null",
    "difficulty": "easy",
    "knowledge_point_ids": [1, 2],
    "created_at": "...",
    "updated_at": "..."
  }
]
```

#### GET /questions/{question_id}
获取单个题目。

**Response (200):** QuestionResponse

**Error:** 404 - Question not found

#### PUT /questions/{question_id}
更新题目。

**Request Body:** 所有字段均可为 null（同 QuestionCreate 字段）

**Response (200):** QuestionResponse

**Error:** 404 - Question not found

#### DELETE /questions/{question_id}
删除题目。

**Response (204):** No Content

**Error:** 404 - Question not found

---

## Students（学生）

#### POST /students
创建学生。

**Request Body:**
```json
{
  "name": "string (required, 1-100 chars)",
  "gender": "enum: male | female | other"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "string",
  "gender": "male",
  "created_at": "...",
  "updated_at": "..."
}
```

#### GET /students
获取学生列表。

**Query Parameters:**
- `skip` (int, default 0)
- `limit` (int, default 20)
- `gender` (enum: male | female | other)

**Response (200):** `list[StudentResponse]`

#### GET /students/{student_id}
获取单个学生。

**Response (200):** StudentResponse

**Error:** 404 - Student not found

#### PUT /students/{student_id}
更新学生。

**Request Body:**
```json
{
  "name": "string | null (1-100 chars)",
  "gender": "enum: male | female | other | null"
}
```

**Response (200):** StudentResponse

**Error:** 404 - Student not found

#### DELETE /students/{student_id}
删除学生。

**Response (204):** No Content

**Error:** 404 - Student not found

---

## Teaching（教学对话）

#### POST /teaching/sessions
开始教学会话。

**Request Body:**
```json
{
  "student_id": "integer (>= 1)",
  "question_content": "string (min_length=1)",
  "question_image": "string | null"
}
```

**Response (201):** TeachingSessionDetailResponse
```json
{
  "id": 1,
  "student_id": 1,
  "status": "active",
  "strategy": "string | null",
  "ended_at": "datetime | null",
  "created_at": "...",
  "updated_at": "...",
  "messages": [
    {
      "id": 1,
      "session_id": 1,
      "role": "user | assistant | system",
      "content": "string",
      "message_type": "question_submit | llm_analysis | student_data | strategy | reference_search | chat",
      "sequence": 0,
      "created_at": "...",
      "updated_at": "...",
      "references": [
        {
          "id": 1,
          "message_id": 1,
          "question_id": 1,
          "similarity_score": 0.85,
          "created_at": "...",
          "updated_at": "..."
        }
      ]
    }
  ]
}
```

#### POST /teaching/sessions/chat
教学对话聊天。

**Request Body:**
```json
{
  "session_id": "integer (>= 1)",
  "message": "string (min_length=1)"
}
```

**Response (200):** TeachingChatResponse
```json
{
  "session_id": 1,
  "assistant_message": {
    "id": 2,
    "session_id": 1,
    "role": "assistant",
    "content": "string",
    "message_type": "chat",
    "sequence": 1,
    "created_at": "...",
    "updated_at": "..."
  }
}
```

**Error:** 400 - Session not found or not active

#### POST /teaching/sessions/end
结束教学会话。

**Request Body:**
```json
{
  "session_id": "integer (>= 1)",
  "mastery_level_delta": "float | null (-1.0 ~ 1.0)"
}
```

**Response (200):** TeachingSessionDetailResponse

**Error:** 404 - Session not found

#### POST /teaching/sessions/{session_id}/cancel
取消教学会话。

**Response (200):** TeachingSessionDetailResponse

**Error:** 404 - Session not found

#### GET /teaching/sessions/{session_id}
获取教学会话详情。

**Response (200):** TeachingSessionDetailResponse

**Error:** 404 - Session not found

---

## Practice（练习）

### Focused Mode

#### POST /practice/sessions/focused
创建 Focused 练习会话。

**Request Body:**
```json
{
  "student_id": "integer (>= 1)",
  "knowledge_point_ids": "list[int] (min_length=1)",
  "difficulty_range": "list[str] (min_length=1, e.g. [\"easy\", \"medium\"])",
  "total_count": "integer (1-100)"
}
```

**Response (201):** StartSessionResponse
```json
{
  "session": {
    "id": 1,
    "mode": "focused",
    "knowledge_point_ids": [1, 2],
    "difficulty_range": ["easy", "medium"],
    "student_id": 1,
    "total_count": 5,
    "started_at": "...",
    "ended_at": null,
    "skip_count": 0,
    "correct_count": 0,
    "wrong_count": 0,
    "skipped_question_ids": [],
    "created_at": "...",
    "updated_at": "..."
  },
  "question": {
    "id": 1,
    "type": "single_choice",
    "content": "string",
    "answer": "string",
    "difficulty": "easy",
    "knowledge_point_ids": [1],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

**Error:** 400 - No questions match the given criteria

### General Mode

#### POST /practice/sessions/general
创建 General 练习会话。

**Request Body:**
```json
{
  "student_id": "integer (>= 1)",
  "knowledge_point_ids": "list[int] (min_length=1)",
  "difficulty_range": "list[str] (min_length=1)"
}
```

**Response (201):** StartSessionResponse（mode 为 general，total_count 初始为 0）

**Error:** 400 - No questions match the given criteria

### 通用端点

#### POST /practice/sessions/{session_id}/submit
提交答案。

**Request Body:**
```json
{
  "question_id": "integer (>= 1)",
  "user_answer": "string (min_length=1)",
  "emotion": "string | null (e.g. \"happy\", \"confused\")"
}
```

**Response (200):** SubmitAnswerResponse
```json
{
  "item": {
    "id": 1,
    "practice_session_id": 1,
    "student_id": 1,
    "question_id": 1,
    "user_answer": "A",
    "sequence": 0,
    "is_correct": true,
    "is_skipped": false,
    "started_at": "...",
    "ended_at": "...",
    "emotion": "happy",
    "created_at": "...",
    "updated_at": "..."
  },
  "is_correct": true,
  "next_question": {
    "id": 2,
    "type": "single_choice",
    "content": "string",
    "answer": "string",
    "difficulty": "medium",
    "knowledge_point_ids": [2],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

- Focused 模式：答完所有题后 `next_question` 为 null
- General 模式：`next_question` 始终为 null

**Error:** 400 - Session not found / Session already ended / Question not found

#### POST /practice/sessions/{session_id}/skip
跳过当前题目（仅 General 模式可用）。

**Request Body:**
```json
{
  "question_id": "integer (>= 1)"
}
```

**Response (200):** NextQuestionResponse
```json
{
  "question": {
    "id": 3,
    "type": "single_choice",
    "content": "string",
    "answer": "string",
    "difficulty": "easy",
    "knowledge_point_ids": [1],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

- 跳过不创建 PracticeItem 记录
- 无更多题目时 `question` 为 null

**Error:** 400 - Skip is only allowed in general mode / Session already ended

#### POST /practice/sessions/{session_id}/next
主动获取下一题。

**Response (200):** NextQuestionResponse

- 已作答/已跳过的题目不会重复出现
- 无更多题目时 `question` 为 null

**Error:** 400 - Session not found / Session already ended

#### POST /practice/sessions/{session_id}/end
结束练习。

**Response (200):** PracticeSessionResponse
- Focused 模式：`total_count` 保持创建时的值
- General 模式：`total_count` 更新为实际作答数（correct + wrong）

**Error:** 400 - Session not found / Session already ended

#### GET /practice/sessions/{session_id}
获取练习详情。

**Response (200):** PracticeSessionDetailResponse
```json
{
  "id": 1,
  "mode": "focused",
  "knowledge_point_ids": [1, 2],
  "difficulty_range": ["easy", "medium"],
  "student_id": 1,
  "total_count": 5,
  "started_at": "...",
  "ended_at": "...",
  "skip_count": 0,
  "correct_count": 3,
  "wrong_count": 2,
  "skipped_question_ids": [],
  "created_at": "...",
  "updated_at": "...",
  "items": [
    {
      "id": 1,
      "practice_session_id": 1,
      "student_id": 1,
      "question_id": 1,
      "user_answer": "A",
      "sequence": 0,
      "is_correct": true,
      "is_skipped": false,
      "started_at": "...",
      "ended_at": "...",
      "emotion": "happy",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

**Error:** 404 - Session not found

---

## 通用字段说明

### 枚举值

| 枚举 | 可选值 |
|---|---|
| QuestionType | `single_choice`, `multiple_choice`, `fill_blank`, `short_answer`, `calculation` |
| Difficulty | `easy`, `medium`, `hard` |
| Gender | `male`, `female`, `other` |
| PracticeMode | `focused`, `general` |
| TeachingSessionStatus | `active`, `completed`, `cancelled` |
| MessageRole | `user`, `assistant`, `system` |
| MessageType | `question_submit`, `llm_analysis`, `student_data`, `strategy`, `reference_search`, `chat` |

### TimestampSchema（通用时间戳）

所有 Response 模型都包含：
- `created_at`: datetime
- `updated_at`: datetime
