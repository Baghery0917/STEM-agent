"""Step 4: align Chinese material onto the OpenStax section tree with DeepSeek.

 a) Tsinghua question bank (clean/tsinghua/questions.jsonl) -> module_id per question
 b) Chinese notes (LinhoNotes, 0112-UniversityPhysics) -> module_id per note chunk

Outputs:
  clean/tsinghua/alignment.jsonl    {id, module_id, confidence}
  clean/notes/chunks.jsonl          {id, source, title, body, module_id, confidence}
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "clean"
CACHE = ROOT / "pipeline/.cache/align"
CACHE.mkdir(parents=True, exist_ok=True)
load_dotenv(ROOT / "pipeline/.env")
client = AsyncOpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=os.environ["DEEPSEEK_BASE_URL"])
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
SEM = asyncio.Semaphore(10)


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf8")]


def dump_jsonl(p, rows):
    with open(p, "w", encoding="utf8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def catalogue() -> tuple[str, set[str]]:
    tree = json.load(open(CLEAN / "openstax/tree.json", encoding="utf8"))
    titles = json.load(open(CLEAN / "openstax/titles_zh.json", encoding="utf8"))
    secs = {s["module_id"]: s for s in load_jsonl(CLEAN / "openstax/sections.jsonl")}
    lines, ids = [], set()
    for v in tree:
        for c in v["chapters"]:
            for m in c["modules"]:
                if secs[m]["title"] == "Introduction":
                    continue
                ids.add(m)
                lines.append(f"{m} | 卷{v['volume']} {titles[c['title']]} | {titles[secs[m]['title']]}")
    return "\n".join(lines), ids


async def chat_json(key: str, system: str, user: str) -> dict:
    f = CACHE / (hashlib.sha1((MODEL + key).encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    async with SEM:
        for attempt in range(4):
            try:
                r = await client.chat.completions.create(model=MODEL, temperature=0, max_tokens=4096,
                                                         response_format={"type": "json_object"},
                                                         messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
                data = json.loads(r.choices[0].message.content)
                f.write_text(json.dumps(data, ensure_ascii=False))
                return data
            except Exception:
                if attempt == 3:
                    raise
                await asyncio.sleep(2 * (attempt + 1))
    return {}


SYS_Q = """你是大学物理教师。下面是 OpenStax《University Physics》的节目录（每行：module_id | 卷与章 | 节名）。
给你一批题目，为每道题选出最匹配的一个 module_id：题目主要考查的知识点所在的节。只能从目录中选。
输出 JSON：{"items": [{"id": 题目id, "module_id": ..., "confidence": 0到1的小数}]}，数量与顺序与输入一致。

目录：
"""

SYS_N = """你是大学物理教师。下面是 OpenStax《University Physics》的节目录（每行：module_id | 卷与章 | 节名）。
给你一批中文笔记片段（标题 + 正文开头），为每个片段选出内容最对应的一个 module_id。只能从目录中选。
输出 JSON：{"items": [{"id": 片段id, "module_id": ..., "confidence": 0到1的小数}]}，数量与顺序与输入一致。

目录：
"""


async def align_batch(system: str, items: list[dict], valid: set[str], key_prefix: str) -> list[dict]:
    user = json.dumps(items, ensure_ascii=False)
    data = await chat_json(key_prefix + user, system, user)
    got = {d["id"]: d for d in data.get("items", [])}
    out = []
    for it in items:
        d = got.get(it["id"], {})
        mid = d.get("module_id", "")
        out.append({"id": it["id"], "module_id": mid if mid in valid else "", "confidence": float(d.get("confidence", 0) or 0)})
    return out


async def align_tsinghua(cat: str, valid: set[str]):
    qs = load_jsonl(CLEAN / "tsinghua/questions.jsonl")
    items = [{"id": q["id"], "chapter": q["chapter_title"], "text": (q["content"][:700] + "\n答案：" + q["answer"][:150])} for q in qs]
    batches = [items[i:i + 15] for i in range(0, len(items), 15)]
    res = await asyncio.gather(*(align_batch(SYS_Q + cat, b, valid, "thu") for b in batches))
    rows = [r for b in res for r in b]
    dump_jsonl(CLEAN / "tsinghua/alignment.jsonl", rows)
    print("tsinghua aligned:", len(rows), "unresolved:", sum(1 for r in rows if not r["module_id"]), "low-confidence(<0.6):", sum(1 for r in rows if r["module_id"] and r["confidence"] < 0.6))


def note_chunks() -> list[dict]:
    chunks = []
    # LinhoNotes: split at ## headings
    for p in sorted((ROOT / "raw/structured/LinhoNotes/大学物理").glob("*/*.md")):
        txt = p.read_text(encoding="utf8")
        h1 = re.search(r"^# (.+)$", txt, flags=re.M)
        file_title = h1.group(1).strip() if h1 else p.stem
        parts = re.split(r"^## ", txt, flags=re.M)
        for i, part in enumerate(parts[1:], 1):
            title, _, body = part.partition("\n")
            body = re.sub(r"!\[\]\(\./images/([^)]+)\)", r"![](notes/linho/\1)", body)
            chunks.append({"id": f"linho-{p.parent.name}-{p.stem}-{i}", "source": "LinhoNotes", "file_title": file_title,
                           "title": title.strip(), "body": body.strip(), "images": re.findall(r"notes/linho/([^)]+)", body)})
    # 0112-UniversityPhysics: chapter-level outline notes + concept atoms
    base = ROOT / "raw/structured/0112-UniversityPhysics"
    for p in sorted(base.glob("PPT/笔记/*/*.md")) + sorted(base.glob("网课（东北大学）/笔记/*/*.md")):
        txt = p.read_text(encoding="utf8")
        parts = re.split(r"^# ", txt, flags=re.M)
        for i, part in enumerate(parts[1:], 1):
            title, _, body = part.partition("\n")
            if len(body.strip()) < 40:
                continue
            chunks.append({"id": f"neu-{p.stem}-{i}", "source": "0112-UniversityPhysics", "file_title": p.stem,
                           "title": title.strip(), "body": body.strip(), "images": []})
    for p in sorted(base.glob("PPT/概念/*/*/相关概念/*.md")):
        txt = p.read_text(encoding="utf8").strip()
        if len(txt) < 40:
            continue
        chap = p.parents[1].name
        chunks.append({"id": "neu-concept-" + hashlib.sha1(str(p).encode()).hexdigest()[:8], "source": "0112-UniversityPhysics",
                       "file_title": chap, "title": p.stem, "body": txt, "images": []})
    return chunks


async def align_notes(cat: str, valid: set[str]):
    chunks = note_chunks()
    items = [{"id": c["id"], "chapter": c["file_title"], "title": c["title"], "text": c["body"][:400]} for c in chunks]
    batches = [items[i:i + 20] for i in range(0, len(items), 20)]
    res = await asyncio.gather(*(align_batch(SYS_N + cat, b, valid, "notes") for b in batches))
    amap = {r["id"]: r for b in res for r in b}
    for c in chunks:
        c["module_id"] = amap[c["id"]]["module_id"]
        c["confidence"] = amap[c["id"]]["confidence"]
    (CLEAN / "notes").mkdir(exist_ok=True)
    dump_jsonl(CLEAN / "notes/chunks.jsonl", chunks)
    print("note chunks:", len(chunks), "unresolved:", sum(1 for c in chunks if not c["module_id"]), "low-confidence:", sum(1 for c in chunks if c["module_id"] and c["confidence"] < 0.6))


async def main():
    cat, valid = catalogue()
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("tsinghua", "all"):
        await align_tsinghua(cat, valid)
    if what in ("notes", "all"):
        await align_notes(cat, valid)


if __name__ == "__main__":
    asyncio.run(main())
