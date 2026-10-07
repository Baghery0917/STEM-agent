"""Step 1: parse OpenStax University Physics CNXML source into clean JSONL.

Outputs (under clean/openstax/):
  tree.json          volumes -> chapters -> sections (module ids, titles, order)
  sections.jsonl     one record per module: markdown body, summary, glossary, media refs
  questions.jsonl    one record per exercise WITH solution: markdown problem/solution, group, type, difficulty
  questions_nosol.jsonl  exercises without solution (kept for reference, not imported)
  glossary.jsonl     term -> meaning (used later as a translation dictionary)
  media/             referenced images copied here
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "raw/structured/openstax-cnxml-source"
OUT = ROOT / "clean/openstax"
MEDIA_OUT = OUT / "media"

NS = {
    "c": "http://cnx.rice.edu/cnxml",
    "m": "http://www.w3.org/1998/Math/MathML",
    "md": "http://cnx.rice.edu/mdml",
    "col": "http://cnx.rice.edu/collxml",
}
C = "{%s}" % NS["c"]
M = "{%s}" % NS["m"]
MD = "{%s}" % NS["md"]
COL = "{%s}" % NS["col"]


def lname(el) -> str:
    return etree.QName(el).localname


# ----------------------------------------------------------------------------
# MathML -> LaTeX
# ----------------------------------------------------------------------------
MO_MAP = {
    "×": r"\times", "·": r"\cdot", "−": "-", "–": "-", "—": "-", "±": r"\pm", "∓": r"\mp",
    "≤": r"\le", "≥": r"\ge", "≠": r"\ne", "≈": r"\approx", "∝": r"\propto", "∞": r"\infty",
    "→": r"\to", "⇒": r"\Rightarrow", "⇔": r"\Leftrightarrow", "←": r"\leftarrow",
    "∑": r"\sum", "∏": r"\prod", "∫": r"\int", "∮": r"\oint", "∂": r"\partial", "∇": r"\nabla",
    "√": r"\sqrt", "°": r"^{\circ}", "′": "'", "″": "''", "⋅": r"\cdot", "∘": r"\circ",
    "∈": r"\in", "∉": r"\notin", "⊂": r"\subset", "∪": r"\cup", "∩": r"\cap", "∀": r"\forall",
    "∼": r"\sim", "≃": r"\simeq", "≡": r"\equiv", "≪": r"\ll", "≫": r"\gg", "⟨": r"\langle",
    "⟩": r"\rangle", "…": r"\ldots", "⋯": r"\cdots", "⋮": r"\vdots", "{": r"\{", "}": r"\}",
    "|": "|", "‖": r"\|", "∠": r"\angle", "⊥": r"\perp", "∥": r"\parallel", "→": r"\to",
    "⇀": r"\rightharpoonup", "∆": r"\Delta", "ℏ": r"\hbar", "↑": r"\uparrow", "↓": r"\downarrow", "〈": r"\langle", "〉": r"\rangle", "∬": r"\iint", "∭": r"\iiint", "≅": r"\cong", "↔": r"\leftrightarrow", "│": "|", "ϒ": r"\Upsilon", "Τ": "T", "：": ":",
}
GREEK = {
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta", "ε": r"\varepsilon", "ϵ": r"\epsilon",
    "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta", "ϑ": r"\vartheta", "ι": r"\iota", "κ": r"\kappa",
    "λ": r"\lambda", "μ": r"\mu", "ν": r"\nu", "ξ": r"\xi", "π": r"\pi", "ρ": r"\rho", "ϱ": r"\varrho",
    "σ": r"\sigma", "ς": r"\varsigma", "τ": r"\tau", "υ": r"\upsilon", "φ": r"\varphi", "ϕ": r"\phi",
    "χ": r"\chi", "ψ": r"\psi", "ω": r"\omega", "Γ": r"\Gamma", "Δ": r"\Delta", "Θ": r"\Theta",
    "Λ": r"\Lambda", "Ξ": r"\Xi", "Π": r"\Pi", "Σ": r"\Sigma", "Υ": r"\Upsilon", "Φ": r"\Phi",
    "Ψ": r"\Psi", "Ω": r"\Omega", "ℏ": r"\hbar", "ℓ": r"\ell", "∞": r"\infty", "∂": r"\partial",
    "∇": r"\nabla", "°": r"^{\circ}",
}
ACCENT = {
    "→": r"\vec", "⇀": r"\vec", "^": r"\hat", "ˆ": r"\hat", "¯": r"\bar", "‾": r"\overline",
    "˙": r"\dot", "¨": r"\ddot", "˜": r"\tilde", "~": r"\tilde", "⃗": r"\vec", "―": r"\overline",
    "_": r"\underline", "⏟": r"\underbrace", "⏞": r"\overbrace", "←": r"\overleftarrow", "↔": r"\overleftrightarrow",
}


def mtext(el) -> str:
    return "".join(el.itertext()).strip()


def wrap(s: str) -> str:
    s = s.strip()
    if len(s) == 1 or (s.startswith("\\") and " " not in s and "{" not in s):
        return s
    return "{" + s + "}"


def mml(el) -> str:
    """Convert a MathML element to LaTeX."""
    tag = lname(el)
    kids = [k for k in el if isinstance(k.tag, str)]
    if tag in ("math", "mrow", "mstyle", "semantics"):
        if tag == "math" and len(kids) == 1 and lname(kids[0]) == "semantics":
            return mml(kids[0])
        if tag == "semantics":
            kids = [k for k in kids if lname(k) != "annotation"]
        return "".join(mml(k) for k in kids)
    if tag == "mi":
        t = mtext(el)
        if t in GREEK:
            return GREEK[t]
        if len(t) > 1 and el.get("mathvariant") != "italic":
            return r"\mathrm{%s}" % t
        return t
    if tag == "mn":
        return mtext(el)
    if tag == "mo":
        t = mtext(el)
        return MO_MAP.get(t, GREEK.get(t, t))
    if tag == "mtext":
        t = "".join(el.itertext())
        if t.strip() == "":
            return r"\ " if t else ""
        return r"\text{%s}" % t.replace("\\", r"\backslash").replace("{", r"\{").replace("}", r"\}")
    if tag == "mspace":
        return r"\,"
    if tag == "msub" and len(kids) == 2:
        return "%s_%s" % (wrap(mml(kids[0])), wrap(mml(kids[1])))
    if tag == "msup" and len(kids) == 2:
        return "%s^%s" % (wrap(mml(kids[0])), wrap(mml(kids[1])))
    if tag == "msubsup" and len(kids) == 3:
        return "%s_%s^%s" % (wrap(mml(kids[0])), wrap(mml(kids[1])), wrap(mml(kids[2])))
    if tag == "mfrac" and len(kids) == 2:
        return r"\frac{%s}{%s}" % (mml(kids[0]), mml(kids[1]))
    if tag == "msqrt":
        return r"\sqrt{%s}" % "".join(mml(k) for k in kids)
    if tag == "mroot" and len(kids) == 2:
        return r"\sqrt[%s]{%s}" % (mml(kids[1]), mml(kids[0]))
    if tag in ("mover", "munder") and len(kids) == 2:
        base, acc = mml(kids[0]), mtext(kids[1])
        if tag == "mover" and acc in ACCENT:
            return "%s{%s}" % (ACCENT[acc], base)
        if tag == "munder" and acc in ("_", "̲", "―"):
            return r"\underline{%s}" % base
        cmd = r"\overset" if tag == "mover" else r"\underset"
        return "%s{%s}{%s}" % (cmd, mml(kids[1]), base)
    if tag == "munderover" and len(kids) == 3:
        return "%s_%s^%s" % (wrap(mml(kids[0])), wrap(mml(kids[1])), wrap(mml(kids[2])))
    if tag == "mtable":
        rows = []
        for tr in kids:
            cells = [mml(td) for td in tr if isinstance(td.tag, str)]
            rows.append(" & ".join(cells))
        ncol = max((r.count("&") for r in rows), default=0) + 1
        return r"\begin{array}{%s}%s\end{array}" % ("l" * ncol, r" \\ ".join(rows))
    if tag in ("mtr", "mtd"):
        return "".join(mml(k) for k in kids)
    if tag == "menclose":
        return r"\boxed{%s}" % "".join(mml(k) for k in kids)
    if tag == "mfenced":
        o, c = el.get("open", "("), el.get("close", ")")
        return "%s%s%s" % (o, ",".join(mml(k) for k in kids), c)
    if tag in ("mphantom",):
        return r"\phantom{%s}" % "".join(mml(k) for k in kids)
    # fallback: concatenate children or text
    return "".join(mml(k) for k in kids) if kids else mtext(el)


def normalise_tex(tex: str) -> str:
    out = []
    for i, seg in enumerate(re.split(r"(\\text\{[^{}]*\})", tex)):
        if i % 2 == 0:
            seg = seg.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'").replace("\u2032", "'")
            seg = "".join(GREEK.get(ch, ch) + (" " if ch in GREEK else "") for ch in seg)
        out.append(seg)
    tex = "".join(out)
    tex = re.sub(r"\\text\{([^{}]*)\}\\text\{([^{}]*)\}", lambda m: "\\text{%s%s}" % (m.group(1), m.group(2)), tex)
    tex = re.sub(r"\\text\{([^{}]*)\}\\text\{([^{}]*)\}", lambda m: "\\text{%s%s}" % (m.group(1), m.group(2)), tex)
    return re.sub(r"\s+", " ", tex).strip()


def math_to_latex(el, display: bool) -> str:
    tex = normalise_tex(mml(el))
    if not tex:
        return ""
    return "$$%s$$" % tex if display else "$%s$" % tex


# ----------------------------------------------------------------------------
# CNXML -> Markdown
# ----------------------------------------------------------------------------
class Ctx:
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.media: list[str] = []
        self.labels: dict[str, str] = {}


def text_of(el, ctx: Ctx) -> str:
    """Inline conversion: returns markdown for an inline-ish element with its tail handled by caller."""
    parts = [el.text or ""]
    for k in el:
        parts.append(inline(k, ctx))
        parts.append(k.tail or "")
    return "".join(parts)


def inline(el, ctx: Ctx) -> str:
    if not isinstance(el.tag, str):
        return ""
    tag = lname(el)
    if el.tag.startswith(M):
        return math_to_latex(el, display=(el.get("display") == "block"))
    if tag == "emphasis":
        eff = el.get("effect", "bold")
        inner = text_of(el, ctx).strip()
        if not inner:
            return ""
        return ("*%s*" if eff == "italics" else "**%s**") % inner
    if tag == "term":
        inner = text_of(el, ctx).strip()
        return "**%s**" % inner if inner else ""
    if tag == "sup":
        return "$^{%s}$" % text_of(el, ctx).strip()
    if tag == "sub":
        return "$_{%s}$" % text_of(el, ctx).strip()
    if tag == "link":
        inner = text_of(el, ctx).strip()
        if inner:
            return inner
        tid = el.get("target-id") or el.get("document") or ""
        return ctx.labels.get(tid, "")
    if tag == "newline":
        return "\n"
    if tag == "footnote":
        return "（注：%s）" % text_of(el, ctx).strip()
    if tag == "span":
        return text_of(el, ctx)
    if tag in ("code", "preformat"):
        return "`%s`" % text_of(el, ctx)
    if tag == "para":
        return block(el, ctx)
    if tag == "list":
        return "\n" + block(el, ctx)
    if tag in ("media", "figure", "image"):
        return block(el, ctx)
    # unknown inline: fall back to text
    return text_of(el, ctx)


def media_block(el, ctx: Ctx) -> str:
    img = el.find(".//" + C + "image")
    alt = el.get("alt", "")
    if img is None:
        return ""
    src = img.get("src", "")
    name = Path(src).name
    ctx.media.append(name)
    return "![%s](media/%s)" % (alt.replace("\n", " ").strip(), name)


def block(el, ctx: Ctx, depth: int = 0) -> str:
    tag = lname(el)
    if tag == "para":
        return clean_ws(text_of(el, ctx))
    if tag == "title":
        return ""
    if tag == "section":
        out = []
        t = el.find(C + "title")
        if t is not None and t.text:
            out.append("#" * min(depth + 2, 6) + " " + clean_ws(text_of(t, ctx)))
        for k in el:
            if isinstance(k.tag, str) and lname(k) != "title":
                b = block(k, ctx, depth + 1)
                if b:
                    out.append(b)
        return "\n\n".join(out)
    if tag == "list":
        ordered = el.get("list-type") == "enumerated"
        items = []
        for i, it in enumerate(el.findall(C + "item"), 1):
            body = clean_ws(text_of(it, ctx)) if not any(lname(k) in ("para", "list") for k in it if isinstance(k.tag, str)) else "\n".join(
                filter(None, [clean_ws(it.text or "")] + [block(k, ctx, depth + 1) if lname(k) in ("para", "list") else inline(k, ctx) + (k.tail or "") for k in it if isinstance(k.tag, str)]))
            items.append(("%d. " % i if ordered else "- ") + body.replace("\n", "\n  "))
        return "\n".join(items)
    if tag == "equation":
        m = el.find(".//" + M + "math")
        if m is None:
            return clean_ws(text_of(el, ctx))
        tex = normalise_tex(mml(m))
        return "$$%s$$" % tex
    if tag == "note":
        cls = el.get("class", "")
        t = el.find(C + "title")
        title = clean_ws(text_of(t, ctx)) if t is not None else ""
        inner = [block(k, ctx, depth + 1) for k in el if isinstance(k.tag, str) and lname(k) != "title"]
        inner = [x for x in inner if x]
        if cls == "equation-callout":
            return "\n\n".join(inner)
        head = "> **%s**" % (title or "注") if cls != "equation-callout" else ""
        body = "\n\n".join(inner).replace("\n", "\n> ")
        return head + "\n>\n> " + body if head else body
    if tag == "example":
        t = el.find(C + "title")
        title = clean_ws(text_of(t, ctx)) if t is not None else "Example"
        inner = [block(k, ctx, depth + 1) for k in el if isinstance(k.tag, str) and lname(k) != "title"]
        return "**例题：%s**\n\n" % title + "\n\n".join(x for x in inner if x)
    if tag == "exercise":
        # in-text check-understanding exercises stay in the section body
        prob = el.find(C + "problem")
        sol = el.find(C + "solution")
        out = []
        if prob is not None:
            out.append("**练习：** " + "\n\n".join(x for x in (block(k, ctx, depth + 1) for k in prob if isinstance(k.tag, str)) if x))
        if sol is not None:
            out.append("**答案：** " + "\n\n".join(x for x in (block(k, ctx, depth + 1) for k in sol if isinstance(k.tag, str)) if x))
        return "\n\n".join(out)
    if tag in ("problem", "solution", "commentary"):
        return "\n\n".join(x for x in (block(k, ctx, depth + 1) for k in el if isinstance(k.tag, str) and lname(k) != "title") if x)
    if tag == "figure":
        parts = []
        for k in el:
            if not isinstance(k.tag, str):
                continue
            kt = lname(k)
            if kt == "media":
                parts.append(media_block(k, ctx))
            elif kt == "caption":
                parts.append("*%s*" % clean_ws(text_of(k, ctx)))
            elif kt == "subfigure":
                parts.append(block(k, ctx, depth + 1))
            elif kt == "title":
                parts.append("**%s**" % clean_ws(text_of(k, ctx)))
        return "\n\n".join(p for p in parts if p)
    if tag == "subfigure":
        parts = [media_block(k, ctx) if lname(k) == "media" else "" for k in el if isinstance(k.tag, str)]
        return "\n\n".join(p for p in parts if p)
    if tag == "media":
        return media_block(el, ctx)
    if tag == "table":
        return table_block(el, ctx)
    if tag == "glossary":
        return ""
    if tag in ("definition",):
        term = el.find(C + "term")
        meaning = el.find(C + "meaning")
        return "**%s**：%s" % (clean_ws(text_of(term, ctx)) if term is not None else "", clean_ws(text_of(meaning, ctx)) if meaning is not None else "")
    if tag == "quote":
        return "> " + clean_ws(text_of(el, ctx))
    if tag in ("preformat", "code"):
        return "```\n%s\n```" % "".join(el.itertext())
    if el.tag.startswith(M):
        return math_to_latex(el, display=True)
    if tag in ("label", "metadata"):
        return ""
    # generic container
    return "\n\n".join(x for x in (block(k, ctx, depth + 1) for k in el if isinstance(k.tag, str)) if x) or clean_ws(text_of(el, ctx))


def table_block(el, ctx: Ctx) -> str:
    rows = []
    for tr in el.iter(C + "row"):
        cells = [clean_ws(text_of(td, ctx)).replace("|", r"\|").replace("\n", " ") for td in tr.findall(C + "entry")]
        rows.append(cells)
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    title = el.find(C + "title")
    out = []
    if title is not None:
        out.append("**%s**" % clean_ws(text_of(title, ctx)))
    out.append("| " + " | ".join(rows[0]) + " |")
    out.append("|" + "---|" * ncol)
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def clean_ws(s: str) -> str:
    s = re.sub(r"[ \t]*\n[ \t]*", " ", s)
    s = re.sub(r" {2,}", " ", s)
    return s.strip()


# ----------------------------------------------------------------------------
# Module parsing
# ----------------------------------------------------------------------------
GROUP_INFO = {
    # class -> (question_type, difficulty)
    "review-conceptual-questions": ("short_answer", "easy"),
    "review-problems": ("calculation", "medium"),
    "review-additional-problems": ("calculation", "medium"),
    "review-challenge": ("calculation", "hard"),
    "check-understanding": ("short_answer", "easy"),
}


def collect_labels(doc, ctx: Ctx):
    """Map element ids to human labels (Figure/Equation/Example numbers are not in source; use generic words)."""
    for el in doc.iter():
        if not isinstance(el.tag, str):
            continue
        i = el.get("id")
        if not i:
            continue
        t = lname(el)
        if t == "figure":
            ctx.labels[i] = "the figure"
        elif t == "equation":
            ctx.labels[i] = "the equation"
        elif t == "example":
            ctx.labels[i] = "the example"
        elif t == "table":
            ctx.labels[i] = "the table"
        elif t == "section":
            tt = el.find(C + "title")
            ctx.labels[i] = ("“%s”" % clean_ws("".join(tt.itertext()))) if tt is not None else ""


def parse_module(mid: str):
    path = SRC / "modules" / mid / "index.cnxml"
    doc = etree.parse(str(path)).getroot()
    ctx = Ctx(mid)
    collect_labels(doc, ctx)
    title = clean_ws("".join(doc.find(C + "title").itertext()))
    meta = doc.find(C + "metadata")
    abstract = ""
    if meta is not None:
        ab = meta.find(MD + "abstract")
        if ab is not None:
            abstract = "\n\n".join(x for x in (block(k, ctx) for k in ab if isinstance(k.tag, str)) if x)
    content = doc.find(C + "content")
    body_parts, summary, key_equations = [], "", ""
    questions = []
    for k in content:
        if not isinstance(k.tag, str):
            continue
        cls = k.get("class", "") or ""
        if lname(k) == "section" and cls in GROUP_INFO and cls != "check-understanding":
            for ex in k.findall(C + "exercise"):
                questions.append(parse_exercise(ex, ctx, cls))
            continue
        if lname(k) == "section" and "key-concepts" in cls:
            summary = "\n\n".join(x for x in (block(c, ctx, 1) for c in k if isinstance(c.tag, str) and lname(c) != "title") if x)
            continue
        if lname(k) == "section" and "key-equations" in cls:
            key_equations = "\n\n".join(x for x in (block(c, ctx, 1) for c in k if isinstance(c.tag, str) and lname(c) != "title") if x)
            continue
        if lname(k) == "glossary":
            continue
        b = block(k, ctx)
        if b:
            body_parts.append(b)
    glossary = []
    g = content.find(C + "glossary") if content is not None else None
    if g is None:
        g = doc.find(C + "glossary")
    if g is not None:
        for d in g.findall(C + "definition"):
            term = d.find(C + "term")
            meaning = d.find(C + "meaning")
            if term is not None and meaning is not None:
                glossary.append({"term": clean_ws(text_of(term, ctx)), "meaning": clean_ws(text_of(meaning, ctx))})
    return {
        "module_id": mid,
        "title": title,
        "abstract": abstract,
        "body": "\n\n".join(body_parts),
        "summary": summary,
        "key_equations": key_equations,
        "glossary": glossary,
        "media": sorted(set(ctx.media)),
    }, questions


def parse_exercise(ex, ctx: Ctx, group: str):
    prob = ex.find(C + "problem")
    sol = ex.find(C + "solution")
    ctx.media_snapshot = len(ctx.media)
    before = len(ctx.media)
    ptxt = block(prob, ctx) if prob is not None else ""
    pmedia = ctx.media[before:]
    before = len(ctx.media)
    stxt = block(sol, ctx) if sol is not None else ""
    smedia = ctx.media[before:]
    qtype, diff = GROUP_INFO[group]
    if qtype == "calculation" and not re.search(r"\d|\$", ptxt + stxt):
        qtype = "short_answer"
    # heuristics: a conceptual question that contains numbers/equations is still short_answer;
    # a "problem" whose solution is a single short token could be fill_blank, keep calculation for now.
    return {
        "id": ex.get("id"),
        "module_id": ctx.module_id,
        "group": group,
        "type": qtype,
        "difficulty": diff,
        "content": ptxt,
        "content_media": pmedia,
        "answer": stxt,
        "answer_media": smedia,
        "has_solution": sol is not None,
    }


# ----------------------------------------------------------------------------
# Collection tree
# ----------------------------------------------------------------------------
def parse_collection(v: int):
    path = SRC / "collections" / f"university-physics-volume-{v}.collection.xml"
    root = etree.parse(str(path)).getroot()
    vol_title = root.find(".//" + MD + "title").text
    content = root.find(COL + "content")
    chapters = []
    order = 0

    def walk(node, unit_title: str | None):
        nonlocal order
        for sub in node.findall(COL + "subcollection"):
            t = sub.find(MD + "title").text
            inner = sub.find(COL + "content")
            has_modules = inner.find(COL + "module") is not None
            if has_modules:
                order += 1
                mods = [(m.get("document")) for m in inner.findall(COL + "module")]
                chapters.append({"title": t, "unit": unit_title, "order": order, "modules": mods})
            else:
                walk(inner, t)

    walk(content, None)
    return {"volume": v, "title": vol_title, "chapters": chapters}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA_OUT.mkdir(exist_ok=True)
    tree = [parse_collection(v) for v in (1, 2, 3)]
    sections_f = open(OUT / "sections.jsonl", "w", encoding="utf8")
    q_f = open(OUT / "questions.jsonl", "w", encoding="utf8")
    qn_f = open(OUT / "questions_nosol.jsonl", "w", encoding="utf8")
    g_f = open(OUT / "glossary.jsonl", "w", encoding="utf8")
    n_sec = n_q = n_qn = n_media = 0
    seen_terms = set()
    for vol in tree:
        for ch in vol["chapters"]:
            for order, mid in enumerate(ch["modules"], 1):
                sec, qs = parse_module(mid)
                sec.update({"volume": vol["volume"], "chapter_order": ch["order"], "chapter_title": ch["title"], "order": order})
                sections_f.write(json.dumps(sec, ensure_ascii=False) + "\n")
                n_sec += 1
                for q in qs:
                    q.update({"volume": vol["volume"], "chapter_order": ch["order"]})
                    if q["has_solution"]:
                        q_f.write(json.dumps(q, ensure_ascii=False) + "\n"); n_q += 1
                    else:
                        qn_f.write(json.dumps(q, ensure_ascii=False) + "\n"); n_qn += 1
                for g in sec["glossary"]:
                    key = g["term"].lower()
                    if key not in seen_terms:
                        seen_terms.add(key)
                        g_f.write(json.dumps({**g, "module_id": mid}, ensure_ascii=False) + "\n")
                for name in sec["media"] + [m for q in qs for m in q["content_media"] + q["answer_media"]]:
                    src = SRC / "media" / name
                    dst = MEDIA_OUT / name
                    if src.exists() and not dst.exists():
                        shutil.copy2(src, dst); n_media += 1
    json.dump(tree, open(OUT / "tree.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(f"sections={n_sec} questions_with_solution={n_q} questions_without={n_qn} glossary_terms={len(seen_terms)} media_copied={n_media}")


if __name__ == "__main__":
    main()
