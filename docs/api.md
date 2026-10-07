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
开始教学会话。流水线在后台执行，前端轮询 GET /teaching/sessions/{id} 直到 `pipeline_status` 为 `done` / `failed`。

**Request Body:**
```json
{
  "student_id": "integer (>= 1)",
  "question_content": "string (min_length=1)",
  "question_image": "string | null",
  "frame_base64": "string | null  (摄像头单帧，仅用于面部情绪识别，不落库)",
  "source_practice_session_id": "integer | null  (从练习转来时填)",
  "source_question_ids": "list[int] | null  (从练习转来的题目；为空则取该练习的星标题)"
}
```

从练习转来时，后端把题干、学生作答与正确答案拼成第一条 `question_submit` 消息，格式：

```
（来自练习 #7）

【练习第 3 题】
<题干>
我的答案：1 m（答错）
正确答案：3 m

<学生附言>
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

#### POST /teaching/sessions/rate
学生对某条 AI 回复的掌握度自评（选填，可取消）。结束会话时若未显式传 `mastery_level_delta`，取最后一条自评映射：0 → −0.1，1 → +0.05，2 → +0.15，3 → +0.25。

**Request Body:**
```json
{
  "session_id": "integer (>= 1)",
  "message_id": "integer (>= 1)",
  "rating": "integer 0-3 | null  (0 还没懂 / 1 看懂了讲解 / 2 能自己做 / 3 能讲给别人；null 取消)"
}
```

**Response (200):** TeachingMessageResponse（含 `self_rating`）

**Error:** 404 - Message not found；400 - Only assistant messages can be rated

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

不再区分专项 / 综合模式。开始时按范围一次性抽满题目，学生可在题目间自由切换，每题都可跳过（计 0 分、不计入档案）。`timed` 只影响前端：计时中不能中途转去提问，只能先星标。

#### POST /practice/match
开始前预估题库里符合范围的题数。

**Request Body:**
```json
{
  "knowledge_point_ids": "list[int] (min_length=1)",
  "difficulty_range": "list[str] (min_length=1)",
  "question_types": "list[str] | null"
}
```

**Response (200):** `{ "matched_count": 37 }`

#### POST /practice/sessions
创建练习会话并一次性抽题。

**Request Body:**
```json
{
  "student_id": "integer (>= 1)",
  "knowledge_point_ids": "list[int] (min_length=1)",
  "difficulty_range": "list[str] (min_length=1)",
  "question_types": "list[str] | null",
  "total_count": "integer (1-100, default 10)",
  "timed": "boolean (default false)",
  "instant_feedback": "boolean (default true)  计时模式忽略此项并强制为 false"
}
```

**Response (201):** StartSessionResponse
```json
{
  "session": {
    "id": 1,
    "timed": true,
    "instant_feedback": false,
    "knowledge_point_ids": [1, 2],
    "difficulty_range": ["easy", "medium"],
    "student_id": 1,
    "total_count": 5,
    "question_ids": [11, 12, 13, 14, 15],
    "starred_question_ids": [],
    "started_at": "...",
    "ended_at": null,
    "skip_count": 0,
    "correct_count": 0,
    "wrong_count": 0,
    "created_at": "...",
    "updated_at": "..."
  },
  "questions": [ { "id": 11, "type": "single_choice", "content": "...", "content_image": null, "difficulty": "easy", "knowledge_point_ids": [1] } ]
}
```

- 题库不足时 `total_count` 按实际抽到的数量返回
- `questions` 不含答案与解析

**Error:** 400 - No questions match the given criteria / Knowledge point ids not found

#### POST /practice/sessions/{session_id}/submit
提交答案。`instant_feedback=true` 时返回对错、答案与解析；否则 `is_correct` / `correct_answer` / `analysis` 为 null（`item.is_correct` 也固定为 false），做完后从 GET 详情看。后台计数不受影响。

**Request Body:**
```json
{
  "question_id": "integer (>= 1)",
  "user_answer": "string (min_length=1)",
  "duration_seconds": "integer | null",
  "frame_base64": "string | null  (提交瞬间的摄像头单帧，只转发给面部情绪识别，不落库)"
}
```

**Response (200):** SubmitAnswerResponse
```json
{
  "item": { "id": 1, "question_id": 11, "user_answer": "A", "is_correct": true, "is_skipped": false, "duration_seconds": 20, "emotion": "自信", "emotion_value": 1.0, "...": "..." },
  "is_correct": true,
  "correct_answer": "A",
  "analysis": "string | null",
  "analysis_image": "string | null",
  "session": { "...": "PracticeSessionResponse，计数已更新" }
}
```

**Error:** 400 - Session not found / Session already ended / Question does not belong to this session / Question already answered in this session

#### POST /practice/sessions/{session_id}/skip
跳过一题（任何模式都可以）。写一条 `is_skipped=true` 的记录，`skip_count` +1，不计入学生档案。

**Request Body:** `{ "question_id": 11, "duration_seconds": 5 }`

**Response (200):** `{ "item": PracticeItemResponse, "session": PracticeSessionResponse }`

#### POST /practice/sessions/{session_id}/star
星标 / 取消星标一题。

**Request Body:** `{ "question_id": 11, "starred": true }`

**Response (200):** PracticeSessionResponse（`starred_question_ids` 已更新）

#### POST /practice/sessions/{session_id}/end
结束练习。未作答的题自动补一条 `is_skipped=true` 记录并计入 `skip_count`；作答题的面部情绪均值回流到涉及知识点的历史情绪，并写一行 `mode=practice` 的情绪流水。

**Response (200):** PracticeSessionResponse

**Error:** 400 - Session not found / Session already ended

#### GET /practice/sessions
学生的练习列表，按开始时间倒序。

**Query Parameters:** `student_id` (int, required), `limit` (1-100, default 20), `offset` (default 0)

**Response (200):** `list[PracticeSessionResponse]`

#### GET /practice/sessions/{session_id}
练习详情：全部题目（不含答案）与作答记录（含题目完整信息，用于回顾）。

**Response (200):** PracticeSessionDetailResponse
```json
{
  "...": "PracticeSessionResponse 字段",
  "questions": [ "QuestionPublicResponse" ],
  "items": [ { "...": "PracticeItemResponse", "question": "QuestionResponse | null" } ]
}
```

**Error:** 404 - Session not found

---

## Search（会话搜索）

#### GET /students/{student_id}/sessions/search
左侧会话栏搜索。教学会话按 user / assistant 消息全文匹配（ILIKE），练习按知识点标题匹配，合并后按时间倒序。

**Query Parameters:** `q` (1-100 字, required), `limit` (1-50, default 20)

**Response (200):**
```json
{
  "q": "摩擦力",
  "hits": [
    { "kind": "teaching", "id": 12, "title": "斜面上的摩擦力方向…", "snippet": "…差在摩擦力的方向…", "at": "...", "status": "active" },
    { "kind": "practice", "id": 7, "title": "摩擦力、牛顿第二定律 · 10 题", "snippet": "摩擦力", "at": "...", "status": "completed" }
  ]
}
```

---

## Evaluation（评价处）

#### GET /students/{student_id}/evaluation
经 MCP 调外部评价服务，只传 `student_id`，评价服务自行读库。契约见 `docs/design/mcp-evaluation-contract.md`。

**Response (200):**
```json
{
  "student_id": 1,
  "evaluation": "string | null",
  "highlights": ["string"],
  "source": "mcp | unavailable",
  "detail": "string | null  (unavailable 时的原因)"
}
```

未配置 `EVALUATION_MCP_URL`、超时或失败都返回 200 + `source=unavailable`，不抛错。

**Error:** 404 - Student not found

---

## Admin Auth（管理台登录）

#### POST /admin/login
口令由环境变量 `ADMIN_PASSWORD` 设置；未设置时返回 403。

**Request Body:** `{ "password": "string" }`

**Response (200):** `{ "token": "string" }`

**Error:** 401 - 口令不正确；403 - 未启用

`/admin/db/*` 全部需要请求头 `X-Admin-Token: <token>`，否则 401。

---

## Report（学习报告）

#### GET /students/{student_id}/report
知识点掌握度、练习/教学统计、情绪趋势与流水，可选 LLM 一段话总结。

**Query Parameters:**
- `mode` (`recent` | `all`, default `recent`)：`recent` 为近 7 天
- `summary` (bool, default true)：是否让 LLM 生成总结；列表页预取时传 false 省一次调用

**Response (200):** StudentReport
```json
{
  "mode": "recent",
  "range_start": "...", "range_end": "...",
  "practice_count": 2, "teaching_count": 1,
  "answered_count": 12, "correct_count": 9,
  "knowledge_points": [
    { "section_id": 1, "section_title": "...", "mastery_level": 0.72, "correct_count": 20, "total_practice_count": 24, "total_teaching_count": 1, "last_practice_at": "...", "last_teaching_at": null, "recent_practice_count": 24, "recent_teaching_count": 1 }
  ],
  "emotion_days": [ { "date": "2026-10-01", "value": 2.1, "count": 3 } ],
  "emotion_logs": [ { "section_id": 1, "section_title": "...", "mode": "teaching", "session_id": 12, "emotion_value": 3.6, "emotion": "受挫", "created_at": "..." } ],
  "summary": "string | null"
}
```

- `emotion_days` 固定 7 天，没有记录的天 `value` 为 null
- `summary` LLM 失败或无学习记录时为 null

**Error:** 404 - Student not found

---

## 通用字段说明

### 枚举值

| 枚举 | 可选值 |
|---|---|
| QuestionType | `single_choice`, `multiple_choice`, `fill_blank`, `short_answer`, `calculation` |
| Difficulty | `easy`, `medium`, `hard` |
| Gender | `male`, `female`, `other` |
| ExplainStyle | `direct`, `guided`, `hint`（学生讲解风格覆盖，PUT /students/{id} 可改） |
| TeachingSessionStatus | `active`, `completed`, `cancelled` |
| MessageRole | `user`, `assistant`, `system` |
| MessageType | `question_submit`, `llm_analysis`, `student_data`, `strategy`, `reference_search`, `chat` |

### TimestampSchema（通用时间戳）

所有 Response 模型都包含：
- `created_at`: datetime
- `updated_at`: datetime

## 物理新闻（落地页）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/news?limit=8` | 公开，只返回 `published=true`，按 `published_on` 倒序 |
| GET | `/api/v1/admin/news` | 管理台，全部，需 `X-Admin-Token` |
| POST | `/api/v1/admin/news` | 新建，字段 title / summary / tag / source / url / published_on / published |
| PUT | `/api/v1/admin/news/{id}` | 部分更新 |
| DELETE | `/api/v1/admin/news/{id}` | 删除 |
