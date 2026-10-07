"""Step 5: assemble the import-ready bundle (clean/bundle/).

  volumes.jsonl   {key, title, description, order}
  chapters.jsonl  {key, volume_key, title, description, order}
  sections.jsonl  {key, chapter_key, title, content, order}
  questions.jsonl {key, section_key, type, content, content_image, answer, answer_image, analysis, difficulty, source}
  media/          all images, referenced from content as /physics-media/<path>

Keys are stable strings (module ids / tsinghua ids) so the importer is idempotent.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "clean"
BUNDLE = CLEAN / "bundle"
MEDIA_URL = "/physics-media"

VOLUME_DESC = {
    1: "力学、波与声学。对应国内大学物理的质点运动学、质点动力学、刚体、振动与波。",
    2: "热学与电磁学。对应气体动理论、热力学基础、静电场、恒定磁场、电磁感应、电磁波。",
    3: "光学与近代物理。对应波动光学、几何光学、狭义相对论、量子物理基础、原子与核物理。",
}


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf8")]


def dump_jsonl(p, rows):
    with open(p, "w", encoding="utf8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


NAME_RE = r"((?:[^()\s]|\([^()\s]*\))+)"


def safe_name(n: str) -> str:
    return n.replace("(", "_").replace(")", "_")


def rewrite_media(text: str, prefix: str) -> str:
    return re.sub(r"\]\((media|figures|notes/linho)/" + NAME_RE + r"\)", lambda m: "](%s/%s/%s)" % (MEDIA_URL, prefix if m.group(1) != "notes/linho" else "notes/linho", safe_name(m.group(2))), text)


def split_choices(content: str) -> str:
    """Turn inline '(A) x (B) y' into separate 'A. x' lines so the practice UI can parse them."""
    m = re.search(r"\(\s*A\s*\)|（\s*A\s*）", content)
    if not m:
        return content
    stem, opts = content[:m.start()].rstrip(), content[m.start():]
    parts = re.split(r"[（(]\s*([A-E])\s*[)）]", opts)
    if len(parts) < 5:
        return content
    lines = []
    for i in range(1, len(parts), 2):
        lines.append("%s. %s" % (parts[i], parts[i + 1].strip().strip("；;")))
    return stem + "\n\n" + "\n".join(lines)


def normalise_note(body: str) -> str:
    """LinhoNotes uses VuePress containers (::: example ... --- ... :::). Convert to plain markdown and demote headings."""
    body = re.sub(r"^:::\s*example[^\n]*$", "**例题**", body, flags=re.M)
    body = re.sub(r"^:::\s*(tip|warning|info|note)[^\n]*$", "**注意**", body, flags=re.M)
    body = re.sub(r"^:::\s*$", "", body, flags=re.M)
    body = re.sub(r"^---\s*$", "**解：**", body, flags=re.M)
    body = re.sub(r"^(#{1,4}) ", lambda m: "#" * min(len(m.group(1)) + 2, 6) + " ", body, flags=re.M)
    return body.strip()


def pull_first_image(content: str, prefix: str) -> tuple[str, str | None]:
    imgs = re.findall(r"!\[[^\]]*\]\(((?:media|figures)/" + NAME_RE + r")\)", content)
    if not imgs:
        return content, None
    first = imgs[0][0]
    content = re.sub(r"\n*!\[[^\]]*\]\(" + re.escape(first) + r"\)\n*", "\n", content, count=1)
    return content.strip(), "%s/%s/%s" % (MEDIA_URL, prefix, safe_name(first.split("/", 1)[1]))


def main():
    BUNDLE.mkdir(parents=True, exist_ok=True)
    tree = json.load(open(CLEAN / "openstax/tree.json", encoding="utf8"))
    titles = json.load(open(CLEAN / "openstax/titles_zh.json", encoding="utf8"))
    secs = {s["module_id"]: s for s in load_jsonl(CLEAN / "openstax/sections.jsonl")}
    secs_zh = {s["module_id"]: s for s in load_jsonl(CLEAN / "openstax/sections_zh.jsonl")}
    notes = defaultdict(list)
    for c in load_jsonl(CLEAN / "notes/chunks.jsonl"):
        if c["module_id"] and c["confidence"] >= 0.6:
            notes[c["module_id"]].append(c)

    volumes, chapters, sections = [], [], []
    for v in tree:
        vk = f"openstax-v{v['volume']}"
        volumes.append({"key": vk, "title": f"第{'一二三'[v['volume'] - 1]}册 · {titles[v['title']].replace('大学物理学 ', '')}", "description": VOLUME_DESC[v["volume"]], "order": v["volume"]})
        for ch in v["chapters"]:
            ck = f"{vk}-ch{ch['order']:02d}"
            unit = titles.get(ch["unit"], ch["unit"]) if ch["unit"] else ""
            chapters.append({"key": ck, "volume_key": vk, "title": f"第{ch['order']}章 {titles[ch['title']]}", "description": (f"单元：{unit}；" if unit else "") + f"OpenStax University Physics Vol.{v['volume']} — {ch['title']}", "order": ch["order"]})
            for order, mid in enumerate(ch["modules"], 0):
                s, z = secs[mid], secs_zh[mid]
                is_intro = s["title"] == "Introduction"
                title = f"{ch['order']}.{order} {z['title_zh']}" if not is_intro else f"{ch['order']}.0 本章导言"
                parts = []
                if z["abstract_zh"]:
                    parts.append("**学习目标**\n\n" + z["abstract_zh"])
                parts.append(z["body_zh"])
                if z["summary_zh"]:
                    parts.append("## 小结\n\n" + z["summary_zh"])
                if z["key_equations_zh"]:
                    parts.append("## 关键公式\n\n" + z["key_equations_zh"])
                if notes.get(mid):
                    parts.append("## 中文笔记补充")
                    for c in notes[mid]:
                        src = "LinhoNotes" if c["source"] == "LinhoNotes" else "东北大学大学物理笔记"
                        parts.append(f"### {c['title']}（来源：{src}）\n\n" + normalise_note(c["body"]))
                content = rewrite_media("\n\n".join(p for p in parts if p), "openstax")
                sections.append({"key": mid, "chapter_key": ck, "title": title, "content": content, "order": order,
                                 "title_en": s["title"], "is_intro": is_intro})

    # questions: OpenStax
    questions = []
    qz = {q["id"]: q for q in load_jsonl(CLEAN / "openstax/questions_zh.jsonl")}
    for q in load_jsonl(CLEAN / "openstax/questions.jsonl"):
        z = qz.get(q["id"])
        if not z:
            continue
        content, img = pull_first_image(z["content_zh"], "openstax")
        answer, aimg = pull_first_image(z["answer_zh"], "openstax")
        questions.append({"key": "openstax-" + q["id"], "section_key": q["module_id"], "type": q["type"],
                          "content": rewrite_media(content, "openstax"), "content_image": img,
                          "answer": rewrite_media(answer, "openstax"), "answer_image": aimg, "analysis": None,
                          "difficulty": q["difficulty"], "source": f"OpenStax University Physics Vol.{q['volume']} / {q['group']}"})
    # questions: Tsinghua
    align = {a["id"]: a for a in load_jsonl(CLEAN / "tsinghua/alignment.jsonl")}
    skipped = 0
    for q in load_jsonl(CLEAN / "tsinghua/questions.jsonl"):
        a = align.get(q["id"])
        if q["status"] != "ok" or not a or not a["module_id"]:
            skipped += 1
            continue
        content = split_choices(q["content"]) if q["qtype"] == "single_choice" else q["content"]
        content, img = pull_first_image(content, "tsinghua")
        answer, aimg = pull_first_image(q["answer"], "tsinghua")
        diff = {"single_choice": "easy", "fill_blank": "medium", "calculation": "hard"}[q["qtype"]]
        questions.append({"key": q["id"], "section_key": a["module_id"], "type": q["qtype"],
                          "content": rewrite_media(content, "tsinghua"), "content_image": img,
                          "answer": rewrite_media(answer, "tsinghua"), "answer_image": aimg,
                          "analysis": rewrite_media(q["analysis"], "tsinghua") or None,
                          "difficulty": diff, "source": f"清华大学《大学物理》习题库 {q['chapter_title']} {q['qtype']} 原编号 {q['source_ref']}"})

    dump_jsonl(BUNDLE / "volumes.jsonl", volumes)
    dump_jsonl(BUNDLE / "chapters.jsonl", chapters)
    dump_jsonl(BUNDLE / "sections.jsonl", sections)
    dump_jsonl(BUNDLE / "questions.jsonl", questions)

    # media
    for sub, src in (("openstax", CLEAN / "openstax/media"), ("tsinghua", CLEAN / "tsinghua/figures")):
        dst = BUNDLE / "media" / sub
        dst.mkdir(parents=True, exist_ok=True)
        for p in src.iterdir():
            if p.is_file() and not (dst / safe_name(p.name)).exists():
                shutil.copy2(p, dst / safe_name(p.name))
    linho = BUNDLE / "media/notes/linho"
    linho.mkdir(parents=True, exist_ok=True)
    for p in (ROOT / "raw/structured/LinhoNotes/大学物理").glob("*/images/*"):
        if not (linho / p.name).exists():
            shutil.copy2(p, linho / p.name)
    from collections import Counter
    print(f"volumes={len(volumes)} chapters={len(chapters)} sections={len(sections)} questions={len(questions)} (tsinghua skipped {skipped})")
    print("types:", Counter(q["type"] for q in questions)); print("difficulty:", Counter(q["difficulty"] for q in questions))
    print("sections with notes:", len(notes), "questions with image:", sum(1 for q in questions if q["content_image"]))


if __name__ == "__main__":
    main()
