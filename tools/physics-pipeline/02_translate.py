"""Step 2: translate OpenStax clean data to Chinese with DeepSeek.

Order: glossary -> chapter/unit titles -> sections (title/abstract/body/summary/key_equations) -> questions.
Every LLM call is cached under pipeline/.cache/translate/<sha1>.json so the script can be re-run.

Usage:
  python 02_translate.py glossary
  python 02_translate.py titles
  python 02_translate.py sections [--limit N]
  python 02_translate.py questions [--limit N]
  python 02_translate.py all
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
CLEAN = ROOT / "clean/openstax"
CACHE = ROOT / "pipeline/.cache/translate"
CACHE.mkdir(parents=True, exist_ok=True)
load_dotenv(ROOT / "pipeline/.env")

client = AsyncOpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=os.environ["DEEPSEEK_BASE_URL"])
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
SEM = asyncio.Semaphore(int(os.environ.get("TRANSLATE_CONCURRENCY", "12")))

SYSTEM = """你是大学物理教材的专业译者，把 OpenStax《University Physics》的英文内容译成简体中文。
严格规则：
1. 只翻译自然语言。所有 LaTeX 公式（$...$ 与 $$...$$ 内的内容）、Markdown 语法、图片链接 ![...](media/...)、表格竖线结构、数字与单位，一律原样保留，不得改动、不得删除、不得新增。图片链接中的 alt 文本翻成中文，括号内路径不变。
2. 物理术语按给定术语表翻译，术语表没有的按国内通用大学物理教材（马文蔚《物理学》、程守洙《普通物理学》）的习惯译法。全文术语保持一致。
3. 译文面向中国理工科大一学生，语句通顺、准确，不加解释，不加译者注，不输出任何额外说明。
4. 保留原文的段落划分、标题层级、列表结构与加粗斜体。
5. 原文中 "the figure" "the equation" "the example" 是对图、式、例题的交叉引用，译为「上图」「上式」「上例」或按语境自然处理。"""


def h(*parts: str) -> str:
    return hashlib.sha1("\x1f".join(parts).encode()).hexdigest()


async def chat(key: str, messages: list[dict], json_mode: bool = False, max_tokens: int = 8192) -> str:
    cache_file = CACHE / (key + ".json")
    if cache_file.exists():
        return json.loads(cache_file.read_text())["content"]
    async with SEM:
        for attempt in range(4):
            try:
                kwargs = dict(model=MODEL, messages=messages, temperature=0.2, max_tokens=max_tokens)
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                r = await client.chat.completions.create(**kwargs)
                content = r.choices[0].message.content or ""
                if r.choices[0].finish_reason == "length":
                    raise RuntimeError("truncated")
                cache_file.write_text(json.dumps({"content": content, "usage": r.usage.model_dump() if r.usage else None}, ensure_ascii=False))
                return content
            except Exception as e:  # noqa: BLE001
                if attempt == 3:
                    raise
                await asyncio.sleep(2 * (attempt + 1))
    return ""


# ----------------------------------------------------------------------------
# glossary
# ----------------------------------------------------------------------------
def load_jsonl(p: Path):
    return [json.loads(l) for l in open(p, encoding="utf8")]


def dump_jsonl(p: Path, rows):
    with open(p, "w", encoding="utf8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


async def translate_glossary():
    rows = load_jsonl(CLEAN / "glossary.jsonl")
    out = []
    batches = [rows[i:i + 40] for i in range(0, len(rows), 40)]

    async def one(batch):
        terms = [r["term"] for r in batch]
        msg = [{"role": "system", "content": "你是大学物理术语译者。给出英文术语及其英文释义，输出 JSON 对象 {\"terms\": [{\"en\": ..., \"zh\": ..., \"meaning_zh\": ...}]}，zh 为国内大学物理教材的标准中文术语（简体），meaning_zh 为释义的中文翻译。保持顺序与数量一致。"},
               {"role": "user", "content": json.dumps([{"en": r["term"], "meaning": r["meaning"]} for r in batch], ensure_ascii=False)}]
        txt = await chat(h("glossary", *terms), msg, json_mode=True)
        data = json.loads(txt)["terms"]
        assert len(data) == len(batch), f"glossary batch size mismatch {len(data)} vs {len(batch)}"
        return [{**r, "term_zh": d["zh"], "meaning_zh": d.get("meaning_zh", "")} for r, d in zip(batch, data)]

    results = await asyncio.gather(*(one(b) for b in batches))
    for r in results:
        out.extend(r)
    dump_jsonl(CLEAN / "glossary_zh.jsonl", out)
    print("glossary translated:", len(out))


def load_glossary_map() -> dict[str, str]:
    p = CLEAN / "glossary_zh.jsonl"
    if not p.exists():
        return {}
    return {r["term"]: r["term_zh"] for r in load_jsonl(p)}


def glossary_hint(text: str, gmap: dict[str, str], limit: int = 60) -> str:
    low = text.lower()
    hits = [(t, z) for t, z in gmap.items() if t.lower() in low]
    hits.sort(key=lambda x: -len(x[0]))
    if not hits:
        return ""
    return "本段涉及的术语表（英文→中文）：\n" + "\n".join(f"{t} → {z}" for t, z in hits[:limit])


# ----------------------------------------------------------------------------
# validation helpers
# ----------------------------------------------------------------------------
def norm_math(m: str) -> str:
    m = m.strip("$").strip()
    m = re.sub(r"[.,;:，。；：]\s*$", "", m)   # trailing punctuation may legitimately move outside $
    return re.sub(r"\s+", "", m)


def signature(text: str):
    maths = [norm_math(m) for m in re.findall(r"\$\$.+?\$\$|\$[^$\n]+?\$", text, flags=re.S)]
    imgs = re.findall(r"\]\((media/[^)]+)\)", text)
    return maths, imgs


def validate(src: str, dst: str) -> list[str]:
    sm, si = signature(src)
    dm, di = signature(dst)
    errs = []
    if sorted(sm) != sorted(dm):
        missing = set(sm) - set(dm)
        extra = set(dm) - set(sm)
        errs.append(f"math mismatch: {len(sm)}->{len(dm)} missing={list(missing)[:3]} extra={list(extra)[:3]}")
    if si != di:
        errs.append(f"image mismatch {si} vs {di}")
    if len(dst) < len(src) * 0.12:
        errs.append("too short")
    return errs


async def translate_text(kind: str, text: str, gmap: dict[str, str], retry_note: str = "") -> tuple[str, list[str]]:
    if not text.strip():
        return "", []
    hint = glossary_hint(text, gmap)
    user = (hint + "\n\n" if hint else "") + retry_note + "请翻译以下内容，只输出译文：\n\n" + text
    key = h("text", kind, MODEL, text, hint, retry_note)
    out = await chat(key, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
    out = out.strip()
    errs = validate(text, out)
    if errs and not retry_note:
        note = "注意：上一次翻译改动了公式或图片链接。所有 $...$、$$...$$ 内的 LaTeX 以及 ![...](media/...) 链接路径必须逐字符原样保留。\n"
        return await translate_text(kind, text, gmap, note)
    return out, errs


def chunk_markdown(body: str, max_chars: int = 7000) -> list[str]:
    paras = body.split("\n\n")
    chunks, cur = [], []
    size = 0
    for p in paras:
        if size + len(p) > max_chars and cur:
            chunks.append("\n\n".join(cur)); cur, size = [], 0
        cur.append(p); size += len(p) + 2
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


# ----------------------------------------------------------------------------
# titles
# ----------------------------------------------------------------------------
async def translate_titles():
    tree = json.load(open(CLEAN / "tree.json", encoding="utf8"))
    secs = load_jsonl(CLEAN / "sections.jsonl")
    items = []
    for v in tree:
        items.append(("volume", v["title"]))
        for c in v["chapters"]:
            items.append(("chapter", c["title"]))
            if c["unit"]:
                items.append(("unit", c["unit"]))
    for s in secs:
        items.append(("section", s["title"]))
    uniq = sorted({t for _, t in items})
    gmap = load_glossary_map()
    msg = [{"role": "system", "content": "你是大学物理教材译者。把下列 OpenStax《University Physics》的册名、单元名、章名、节名译成简体中文，用国内大学物理教材的习惯表述（如 Newton's Laws of Motion → 牛顿运动定律，Gauss's Law → 高斯定理，Electric Potential → 电势）。输出 JSON 对象 {\"titles\": {英文: 中文, ...}}，键必须与输入完全一致。"},
           {"role": "user", "content": json.dumps(uniq, ensure_ascii=False)}]
    txt = await chat(h("titles", MODEL, *uniq), msg, json_mode=True)
    m = json.loads(txt)["titles"]
    missing = [t for t in uniq if t not in m]
    assert not missing, missing
    json.dump(m, open(CLEAN / "titles_zh.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("titles translated:", len(m))


# ----------------------------------------------------------------------------
# sections
# ----------------------------------------------------------------------------
async def translate_sections(limit: int | None):
    secs = load_jsonl(CLEAN / "sections.jsonl")
    if limit:
        secs = secs[:limit]
    gmap = load_glossary_map()
    titles = json.load(open(CLEAN / "titles_zh.json", encoding="utf8"))
    out_path = CLEAN / "sections_zh.jsonl"
    done = {r["module_id"] for r in load_jsonl(out_path)} if out_path.exists() and not limit else set()
    results = {}

    async def one(s):
        if s["module_id"] in done:
            return
        errs = []
        rec = {"module_id": s["module_id"], "title_zh": titles.get(s["title"], s["title"])}
        for field in ("abstract", "summary", "key_equations"):
            rec[field + "_zh"], e = await translate_text(field, s[field], gmap)
            errs += [f"{field}: {x}" for x in e]
        chunks = chunk_markdown(s["body"])
        parts = await asyncio.gather(*(translate_text("body", c, gmap) for c in chunks))
        rec["body_zh"] = "\n\n".join(p for p, _ in parts)
        for i, (_, e) in enumerate(parts):
            errs += [f"body[{i}]: {x}" for x in e]
        rec["errors"] = errs
        results[s["module_id"]] = rec
        print(f"  {s['module_id']} {s['title']} chunks={len(chunks)} errors={len(errs)}", flush=True)

    await asyncio.gather(*(one(s) for s in secs))
    mode = "a" if done else "w"
    with open(out_path, mode, encoding="utf8") as f:
        for s in secs:
            if s["module_id"] in results:
                f.write(json.dumps(results[s["module_id"]], ensure_ascii=False) + "\n")
    print("sections translated:", len(results), "with errors:", sum(1 for r in results.values() if r["errors"]))


# ----------------------------------------------------------------------------
# questions
# ----------------------------------------------------------------------------
async def translate_questions(limit: int | None):
    qs = load_jsonl(CLEAN / "questions.jsonl")
    if limit:
        qs = qs[:limit]
    gmap = load_glossary_map()
    out_path = CLEAN / "questions_zh.jsonl"
    done = {r["id"] for r in load_jsonl(out_path)} if out_path.exists() and not limit else set()
    todo = [q for q in qs if q["id"] not in done]
    results = {}

    async def one(q):
        c, e1 = await translate_text("question", q["content"], gmap)
        a, e2 = await translate_text("answer", q["answer"], gmap)
        results[q["id"]] = {"id": q["id"], "content_zh": c, "answer_zh": a, "errors": e1 + e2}

    for i in range(0, len(todo), 200):
        await asyncio.gather(*(one(q) for q in todo[i:i + 200]))
        print(f"  questions {min(i + 200, len(todo))}/{len(todo)}", flush=True)
    with open(out_path, "a" if done else "w", encoding="utf8") as f:
        for q in todo:
            f.write(json.dumps(results[q["id"]], ensure_ascii=False) + "\n")
    print("questions translated:", len(results), "with errors:", sum(1 for r in results.values() if r["errors"]))


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    if cmd in ("glossary", "all"):
        await translate_glossary()
    if cmd in ("titles", "all"):
        await translate_titles()
    if cmd in ("sections", "all"):
        await translate_sections(limit)
    if cmd in ("questions", "all"):
        await translate_questions(limit)


if __name__ == "__main__":
    asyncio.run(main())
