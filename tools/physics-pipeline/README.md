# 大学物理数据流水线

把 OpenStax《University Physics》三卷（CC BY 4.0）作为知识树主干，翻成中文，再把清华大学物理题库和两套中文笔记对齐到节，最后导入 STEM-agent 的 PostgreSQL。

## 目录

```
physics-data/
  raw/            原始资料（见 ../SOURCES.md）
  clean/
    openstax/     解析与翻译中间产物：tree.json, sections*.jsonl, questions*.jsonl, glossary*.jsonl, titles_zh.json, media/
    tsinghua/     清华题库 795 题 questions.jsonl + alignment.jsonl + figures/
    notes/        中文笔记切片 chunks.jsonl（已挂 module_id）
    bundle/       入库包：volumes / chapters / sections / questions 四个 jsonl + media/
  pipeline/
    .env          DEEPSEEK_API_KEY（不入库）
    .cache/       每次 LLM 调用的缓存，按内容哈希命名，重跑不重复花钱
    01..06_*.py   见下
```

## 步骤

| 脚本 | 作用 | 产物 | 需要 LLM |
|---|---|---|---|
| 01_parse_openstax.py | CNXML + MathML 转 Markdown + KaTeX；抽章末习题；复制图片 | clean/openstax/ | 否 |
| 02_translate.py | 术语表 → 标题 → 节正文 → 题目，逐条校验公式与图片链接未被改动 | *_zh.jsonl | DeepSeek |
| 03_parse_tsinghua.py | 清华题库 tex 转 Markdown；官方答案与后补解析交叉校验，冲突题标 review | clean/tsinghua/ | 否 |
| 04_align.py | 清华题与中文笔记切片归到 OpenStax 节 | alignment.jsonl, notes/chunks.jsonl | DeepSeek |
| 05_build_bundle.py | 拼装册章节与题目；选择题拆成 `A. ` 行；首图进 content_image；图片路径改为 /physics-media/… | clean/bundle/ | 否 |
| 06_import_db.py | 幂等导入 Postgres（physics_import_keys 记录 key→id）；可选算 embedding | 数据库 | 可选 |

```
.venv/bin/python pipeline/01_parse_openstax.py
.venv/bin/python pipeline/02_translate.py all
.venv/bin/python pipeline/03_parse_tsinghua.py
.venv/bin/python pipeline/04_align.py all
.venv/bin/python pipeline/05_build_bundle.py
.venv/bin/python pipeline/06_import_db.py --dsn postgresql://postgres:postgres@127.0.0.1:5432/stem_db [--embed]
```

## 入库后还要做的两件事

1. **静态图片**：bundle 里所有图片引用都是 `/physics-media/<openstax|tsinghua|notes/linho>/<file>`。把 `clean/bundle/media/` 挂到前端同源的 `/physics-media/` 路径下（nginx `location /physics-media/ { alias ...; }`，或开发时放进 `frontend/public/physics-media/`）。
2. **embedding**：`--embed` 用 STEM-agent/backend/.env 里的 DashScope key 批量算 text-embedding-v4，3106 题约 10 分钟。不加该参数 embedding 为空，相似题检索不可用，其余功能不受影响。

## 已知问题

- 清华题库有 14 题官方答案与后补解析数值冲突，标为 review 未入库，名单在 clean/tsinghua/questions.jsonl 的 `status=review`。
- 清华题库的解析（思路/做法/易错点）是上游仓库用 LLM 补写的，上游审计报告列出过错配案例；入库题只校验了选择题字母和填空题数值一致，计算题解析未逐题核对。
- OpenStax 2325 题的难度按题组粗分：概念题 easy、计算题 medium、挑战题 hard；清华题按题型分：选择 easy、填空 medium、计算 hard。
- 翻译把 `\text{Sum of displacements}` 这类公式内英文也翻成了中文，校验器已放行；公式内英文变量名未受影响。
- 314 节中 44 节是 OpenStax 的章导言，只有一段话和一张图，入库时标题统一为「N.0 本章导言」。
