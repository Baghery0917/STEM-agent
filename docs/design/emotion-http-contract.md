# 面部情绪识别 HTTP 契约

教学 / 练习流程在拿到摄像头截帧后，调用外部情绪识别服务，得到五档分类，映射为数值 1–5 写入消息或练习明细。
调用方是 `backend/app/external/emotion.py`。

> 本服务**不连 STEM 数据库**；只需实现 HTTP `/recognize`。对接总览见 [`../external-interfaces.md`](../external-interfaces.md) §3。策略 / 评价服务的只读连库见该文档 §0。

## 传输

- 协议：HTTP `POST`
- 路径：`{EMOTION_BASE_URL}/recognize`  
  例：`EMOTION_BASE_URL=http://emotion:8300` → `POST http://emotion:8300/recognize`
- Content-Type：`multipart/form-data`
- 鉴权：可选。配置 `EMOTION_API_KEY` 时，后端带 `Authorization: Bearer <key>`
- 超时：默认 3 秒（`EMOTION_TIMEOUT_SECONDS`），超时或失败则本帧情绪记空，**不重试、不中断**主流程

## 请求

| 字段 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `image` | multipart file | JPEG 字节流 | 是 | 文件名任意（后端发 `frame.jpg`），`Content-Type: image/jpeg` |
| `student_id` | multipart form | string（数字） | 否 | 学生 id，便于服务侧日志 / 个性化；可忽略 |

## 响应

HTTP 200，`application/json`：

```json
{
  "emotion": "confident",
  "confidence": 0.92
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `emotion` | string | 是 | 五档之一，大小写不敏感，后端会 `.lower()` |
| `confidence` | number | 否 | 0.0–1.0；缺省按 `1.0` |

### `emotion` 枚举（必须严格使用下列值）

| 值 | 数值映射 | 中文标签（系统内） |
|----|----------|-------------------|
| `confident` | 1 | 自信 |
| `slightly_uncertain` | 2 | 略犹豫 |
| `discouraged` | 3 | 气馁 |
| `frustrated` | 4 | 受挫 |
| `very_frustrated` | 5 | 非常受挫 |

其他字符串会导致客户端解析失败，本帧情绪记空。

## 调用时机（本系统侧）

| 场景 | 何时调用 |
|------|----------|
| 教学模式 | 学生发消息且携带 `frame_base64` 时 |
| 练习模式 | 学生提交答案且携带 `frame_base64` 时 |

无帧或未配置 `EMOTION_BASE_URL`：不调用，情绪字段为空。

## 失败时后端的行为

- URL 未配置、HTTP 非 2xx、超时、JSON 非法、`emotion` 非法：记 warning，本帧 `facial_value` 为空
- 教学侧仍可用文本情绪（LLM）做混合；练习侧该题情绪可为空
- **绝不**因情绪服务失败而中断教学 / 练习主流程

## 环境变量

| 变量 | 说明 |
|------|------|
| `EMOTION_BASE_URL` | 服务根地址（不含 `/recognize`） |
| `EMOTION_API_KEY` | 可选 Bearer token |
| `EMOTION_TIMEOUT_SECONDS` | 默认 `3` |

## 与文本情绪的关系（供对照，非本契约范围）

文本情绪由本仓库 LLM 在教学路径内完成，**不是**外部 HTTP 服务。教学混合公式默认：

`emotion_value = 0.6 × facial + 0.4 × text`（`EMOTION_FACIAL_WEIGHT`）

## 联调建议

最小可用实现：固定返回 `{"emotion":"confident","confidence":1.0}` 即可打通链路。  
可按 JPEG 大小 / `student_id` 轮换五档，便于前端徽章验证。
