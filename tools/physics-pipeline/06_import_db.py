"""Step 6: import clean/bundle into the STEM-agent PostgreSQL database.

Idempotent: a mapping table physics_import_keys(key, kind, row_id) is created on first run; rows whose key
already exists are updated in place instead of duplicated.

Usage:
  python 06_import_db.py --dsn postgresql://postgres:postgres@127.0.0.1:5432/stem_db [--dry-run] [--embed]

--embed computes question embeddings through the backend's DashScope-compatible endpoint using
LLM_BASE_URL / LLM_API_KEY / LLM_EMBEDDING_MODEL from STEM-agent/backend/.env. Without it, embedding stays NULL.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "clean/bundle"
BACKEND_ENV = ROOT.parent / "STEM-agent/backend/.env"


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf8")]


def strip_math(text: str) -> str:
    t = re.sub(r"\$\$.+?\$\$", " ", text, flags=re.S)
    t = re.sub(r"\$.+?\$", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def embed_texts(texts: list[str]) -> list[list[float] | None]:
    from dotenv import dotenv_values
    from openai import OpenAI
    cfg = dotenv_values(BACKEND_ENV) if BACKEND_ENV.exists() else {}
    key, base, model = cfg.get("LLM_API_KEY"), cfg.get("LLM_BASE_URL"), cfg.get("LLM_EMBEDDING_MODEL", "text-embedding-v4")
    if not key:
        print("  no LLM_API_KEY in backend/.env, skipping embeddings"); return [None] * len(texts)
    client = OpenAI(api_key=key, base_url=base)
    out: list[list[float] | None] = []
    for i in range(0, len(texts), 10):
        batch = [strip_math(t)[:2000] or " " for t in texts[i:i + 10]]
        r = client.embeddings.create(model=model, input=batch, dimensions=1024)
        out += [d.embedding for d in r.data]
        if (i // 10) % 20 == 0:
            print(f"  embedded {min(i + 10, len(texts))}/{len(texts)}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default=os.environ.get("DATABASE_URL_SYNC", "postgresql://postgres:postgres@127.0.0.1:5432/stem_db"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--embed", action="store_true")
    a = ap.parse_args()

    volumes, chapters, sections, questions = (load_jsonl(BUNDLE / f) for f in ("volumes.jsonl", "chapters.jsonl", "sections.jsonl", "questions.jsonl"))
    print(f"bundle: {len(volumes)} volumes, {len(chapters)} chapters, {len(sections)} sections, {len(questions)} questions")
    if a.dry_run:
        return
    conn = psycopg2.connect(a.dsn)
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS physics_import_keys (
        key TEXT PRIMARY KEY, kind TEXT NOT NULL, row_id INTEGER NOT NULL)""")
    cur.execute("SELECT key, kind, row_id FROM physics_import_keys")
    ids = {(k, kind): rid for k, kind, rid in cur.fetchall()}

    def upsert(kind, key, insert_sql, insert_args, update_sql, update_args):
        rid = ids.get((key, kind))
        if rid:
            cur.execute(update_sql, (*update_args, rid))
        else:
            cur.execute(insert_sql, insert_args)
            rid = cur.fetchone()[0]
            cur.execute("INSERT INTO physics_import_keys(key, kind, row_id) VALUES (%s,%s,%s)", (key, kind, rid))
            ids[(key, kind)] = rid
        return rid

    for v in volumes:
        upsert("volume", v["key"],
               'INSERT INTO volumes(title, description, "order") VALUES (%s,%s,%s) RETURNING id', (v["title"], v["description"], v["order"]),
               'UPDATE volumes SET title=%s, description=%s, "order"=%s, updated_at=now() WHERE id=%s', (v["title"], v["description"], v["order"]))
    for c in chapters:
        vid = ids[(c["volume_key"], "volume")]
        upsert("chapter", c["key"],
               'INSERT INTO chapters(volume_id, title, description, "order") VALUES (%s,%s,%s,%s) RETURNING id', (vid, c["title"], c["description"], c["order"]),
               'UPDATE chapters SET volume_id=%s, title=%s, description=%s, "order"=%s, updated_at=now() WHERE id=%s', (vid, c["title"], c["description"], c["order"]))
    for s in sections:
        cid = ids[(s["chapter_key"], "chapter")]
        upsert("section", s["key"],
               'INSERT INTO sections(chapter_id, title, content, "order") VALUES (%s,%s,%s,%s) RETURNING id', (cid, s["title"], s["content"], s["order"]),
               'UPDATE sections SET chapter_id=%s, title=%s, content=%s, "order"=%s, updated_at=now() WHERE id=%s', (cid, s["title"], s["content"], s["order"]))
    conn.commit()
    print("knowledge tree committed")

    vectors = embed_texts([q["content"] for q in questions]) if a.embed else [None] * len(questions)
    for q, vec in zip(questions, vectors):
        sid = ids[(q["section_key"], "section")]
        vec_s = None if vec is None else "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        qid = upsert("question", q["key"],
                     "INSERT INTO questions(type, content, content_image, answer, answer_image, analysis, difficulty, embedding) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                     (q["type"], q["content"], q["content_image"], q["answer"], q["answer_image"], q["analysis"], q["difficulty"], vec_s),
                     "UPDATE questions SET type=%s, content=%s, content_image=%s, answer=%s, answer_image=%s, analysis=%s, difficulty=%s, embedding=COALESCE(%s, embedding), updated_at=now() WHERE id=%s",
                     (q["type"], q["content"], q["content_image"], q["answer"], q["answer_image"], q["analysis"], q["difficulty"], vec_s))
        cur.execute("DELETE FROM question_knowledge_points WHERE question_id=%s", (qid,))
        cur.execute("INSERT INTO question_knowledge_points(question_id, section_id) VALUES (%s,%s)", (qid, sid))
    conn.commit()
    print("questions committed:", len(questions))


if __name__ == "__main__":
    main()
