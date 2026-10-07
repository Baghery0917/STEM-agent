"""Step 3: parse the Tsinghua physics question bank (LaTeX, 795 problems) into clean JSONL.

Input : raw/structured/college-physics-a1-notes/question-banks/tsinghua-physics-latex/chapters/NN-generated.tex
Output: clean/tsinghua/questions.jsonl, clean/tsinghua/figures/

Each record: id, chapter (01..10), chapter_title, qtype, number, content (markdown+katex), answer, analysis,
             source_ref, figures, flags (list of QA flags), status ("ok" | "review")
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "raw/structured/college-physics-a1-notes/question-banks/tsinghua-physics-latex"
OUT = ROOT / "clean/tsinghua"
FIG_OUT = OUT / "figures"

TYPE_MAP = {"选择题": "single_choice", "填空题": "fill_blank", "计算题": "calculation"}

# ----------------------------------------------------------------------------
# LaTeX -> Markdown + KaTeX
# ----------------------------------------------------------------------------
MACROS = {
    r"\dd": r"\mathrm{d}", r"\ee": r"\mathrm{e}", r"\ii": r"\mathrm{i}",
    r"\formulaobject": r"\square",
}


def replace_balanced(s: str, cmd: str, fn) -> str:
    """Replace every cmd{...} (brace-balanced) with fn(inner)."""
    out, i = [], 0
    while True:
        j = s.find(cmd + "{", i)
        if j < 0:
            out.append(s[i:]); break
        out.append(s[i:j])
        k, depth = j + len(cmd) + 1, 1
        while k < len(s) and depth:
            if s[k] == "{": depth += 1
            elif s[k] == "}": depth -= 1
            k += 1
        out.append(fn(s[j + len(cmd) + 1:k - 1]))
        i = k
    return "".join(out)


def tex_to_md(s: str, figures: list[str]) -> str:
    s = s.replace("\r", "")
    # figures
    def fig(m):
        name = m.group(1).strip()
        figures.append(name)
        return "\n\n![](figures/%s)\n\n" % name
    s = re.sub(r"\\begin\{center\}\s*\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}\s*\\end\{center\}", fig, s)
    s = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", fig, s)
    s = re.sub(r"\\missingfigure\{[^}]*\}", "\n\n（原题附图缺失）\n\n", s)
    # math delimiters
    s = re.sub(r"\\\[(.*?)\\\]", lambda m: "\n\n$$" + m.group(1).strip() + "$$\n\n", s, flags=re.S)
    s = re.sub(r"\\\((.*?)\\\)", lambda m: "$" + m.group(1).strip() + "$", s, flags=re.S)
    s = re.sub(r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}", lambda m: "\n\n$$" + m.group(2).strip() + "$$\n\n", s, flags=re.S)
    s = replace_balanced(s, r"\ensuremath", lambda inner: "$" + inner + "$")
    # 2×10${}^{-6}$ style superscripts written as separate math: fold into one math group when preceded by digits
    s = re.sub(r"(\d+)\s*\$\{\}\^\{([^{}$]*)\}\$", r"$\1^{\2}$", s)
    s = re.sub(r"\$([^$\n]+)\$\s*\$\{\}([_^])\{([^{}$]*)\}\$", r"$\1\2{\3}$", s)
    s = re.sub(r"([A-Za-z])\s*\$\{\}([_^])\{([^{}$]*)\}\$", r"$\1\2{\3}$", s)
    s = re.sub(r"\$\{\}\^\{\{-\}\{(\d+)\}\}\$", r"$^{-\1}$", s)
    s = re.sub(r"\^\{\{-\}\{(\d+)\}\}", r"^{-\1}", s)
    # custom macros
    for k, v in MACROS.items():
        s = s.replace(k, v)
    s = re.sub(r"\\vect\{([^}]*)\}", r"\\boldsymbol{\1}", s)
    s = re.sub(r"\\answerblank\{[^}]*\}", "______", s)
    s = re.sub(r"\\problemref\{[^}]*\}", "", s)
    s = re.sub(r"\\reviewmark", "", s)
    s = re.sub(r"\\unofficialanswer\{((?:[^{}]|\{[^{}]*\})*)\}", r"\1", s)
    s = re.sub(r"\\todocheck\{((?:[^{}]|\{[^{}]*\})*)\}", r"【待核对：\1】", s)
    # text formatting (outside math is the common case; inside math \textbf is rare in this corpus)
    s = re.sub(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}", r"**\1**", s)
    s = re.sub(r"\\textit\{((?:[^{}]|\{[^{}]*\})*)\}", r"*\1*", s)
    s = re.sub(r"\\emph\{((?:[^{}]|\{[^{}]*\})*)\}", r"*\1*", s)
    s = re.sub(r"\\underline\{((?:[^{}]|\{[^{}]*\})*)\}", r"<u>\1</u>", s)
    s = re.sub(r"\\textcolor\{[^}]*\}\{((?:[^{}]|\{[^{}]*\})*)\}", r"\1", s)
    # spacing / layout commands outside math
    s = re.sub(r"\\(quad|qquad|hfill|noindent|par|newline|smallskip|medskip|bigskip|centering|vspace\*?\{[^}]*\}|hspace\*?\{[^}]*\}|linebreak|clearpage|newpage)\b", " ", s)
    s = s.replace("\\\\", "\n")
    s = re.sub(r"\\begin\{(center|flushleft|flushright|minipage)\}(\[[^\]]*\])?(\{[^}]*\})?", "", s)
    s = re.sub(r"\\end\{(center|flushleft|flushright|minipage)\}", "", s)
    # itemize/enumerate
    s = re.sub(r"\\begin\{(itemize|enumerate)\}(\[[^\]]*\])?", "\n", s)
    s = re.sub(r"\\end\{(itemize|enumerate)\}", "\n", s)
    s = re.sub(r"^\s*\\item\s*", "- ", s, flags=re.M)
    # escapes
    s = s.replace(r"\%", "%").replace(r"\&", "&").replace(r"\_", "_").replace(r"\#", "#").replace("~", " ")
    s = s.replace(r"\{", "{").replace(r"\}", "}") if "$" not in s else s
    # tidy
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# ----------------------------------------------------------------------------
# answer extraction and QA flags
# ----------------------------------------------------------------------------
def extract_analysis_answer(analysis_tex: str) -> str:
    m = re.search(r"\\textbf\{答案[:：]\}\s*(.+?)(?:\n\s*\n|\\textbf\{思路|\\textbf\{做法|$)", analysis_tex, flags=re.S)
    return m.group(1).strip() if m else ""


def choice_letters(s: str) -> list[str]:
    s = re.sub(r"\$[^$]*\$", " ", s)
    return re.findall(r"(?<![A-Za-z])([A-D])(?![A-Za-z])", s)


def norm_numeric(s: str) -> list[float]:
    s = s.replace("×", "x").replace("\\times", "x").replace("\\cdot", "x").replace("{", "").replace("}", "").replace("$", "").replace("\\,", "")
    s = re.sub(r"[.．,，;；]\s*$", "", s)
    nums = []
    for m in re.finditer(r"(-?\d+(?:\.\d+)?)\s*(?:x\s*10\s*\^\s*\(?(-?\d+)\)?)?", s):
        v = float(m.group(1))
        if m.group(2):
            v *= 10 ** int(m.group(2))
        nums.append(v)
    return nums


OCR_RESIDUE = re.compile(r"(?:(?<![A-Za-z\\])[A-Z](?![A-Za-z])\s*){5,}")


def qa_flags(qtype: str, content: str, official: str, analysis: str, analysis_ans: str) -> list[str]:
    flags = []
    if not official.strip() or official.strip() in ("$\\,$", "$ $", "；", ";"):
        flags.append("official_empty")
    if qtype == "single_choice":
        o, a = choice_letters(official), choice_letters(analysis_ans)
        if o and a and o[0] != a[0]:
            flags.append(f"choice_conflict:{o[0]}vs{a[0]}")
        if not re.search(r"\(A\)|（A）|\bA[.．、]", content):
            flags.append("no_options")
    elif qtype == "fill_blank":
        on, an = norm_numeric(official), norm_numeric(analysis_ans)
        if on and an:
            o0, a0 = on[0], an[0]
            if a0 != 0 and o0 != 0 and not (0.5 < abs(o0 / a0) < 2.0) and abs(o0 - a0) > 1e-9:
                flags.append(f"numeric_conflict:{o0}vs{a0}")
    plain = re.sub(r"\$[^$]*\$", " ", content)
    if OCR_RESIDUE.search(plain):
        flags.append("ocr_residue")
    if "缺失" in content or "missingfigure" in content:
        flags.append("missing_figure")
    if "【待核对" in content + official + analysis:
        flags.append("todo_check")
    if len(content.strip()) < 15:
        flags.append("content_too_short")
    return flags


# ----------------------------------------------------------------------------
# parsing
# ----------------------------------------------------------------------------
BOX = re.compile(r"\\begin\{problembox\}\{([^}]*)\}(.*?)\\end\{problembox\}\s*\\begin\{officialbox\}(.*?)\\end\{officialbox\}\s*(?:\\begin\{analysisbox\}(.*?)\\end\{analysisbox\})?", re.S)


def parse_chapter(path: Path):
    tex = path.read_text(encoding="utf8")
    ch_num = path.name[:2]
    ch_title = re.search(r"\\chapter\{\d+\s*([^}]*)\}", tex).group(1).strip()
    records = []
    # split by \section
    parts = re.split(r"\\section\{([^}]*)\}", tex)
    for i in range(1, len(parts), 2):
        sec_name, body = parts[i].strip(), parts[i + 1]
        qtype = TYPE_MAP.get(sec_name, "short_answer")
        for m in BOX.finditer(body):
            label, prob, official, analysis = m.group(1), m.group(2), m.group(3), m.group(4) or ""
            num = int(re.search(r"\d+", label).group(0))
            ref = re.search(r"\\problemref\{[^0-9]*(\d+)\}", prob)
            source_ref = ref.group(1) if ref else ""
            figs: list[str] = []
            content = tex_to_md(prob, figs)
            answer = tex_to_md(official, figs)
            analysis_ans_tex = extract_analysis_answer(analysis)
            analysis_md = tex_to_md(analysis, figs)
            # analysis: drop the duplicated "答案" line, keep 思路/做法/易错点
            analysis_md = re.sub(r"^\*\*答案[:：]\*\*.*?(?=\n\*\*|\Z)", "", analysis_md, count=1, flags=re.S).strip()
            analysis_ans_md = tex_to_md(analysis_ans_tex, [])
            flags = qa_flags(qtype, content, answer, analysis, analysis_ans_md)
            if qtype == "single_choice" and not choice_letters(answer) and choice_letters(analysis_ans_tex):
                answer = choice_letters(analysis_ans_tex)[0]
                flags.append("answer_from_analysis")
            answer = re.sub(r"^\s*([A-D])\s*[；;。.]?\s*$", r"\1", answer)
            records.append({
                "id": f"thu-{ch_num}-{qtype}-{num:03d}",
                "chapter": ch_num,
                "chapter_title": ch_title,
                "qtype": qtype,
                "number": num,
                "source_ref": source_ref,
                "content": content,
                "answer": answer,
                "analysis": analysis_md,
                "figures": figs,
                "flags": flags,
                "status": "review" if any(f.split(":")[0] in ("official_empty", "choice_conflict", "numeric_conflict", "ocr_residue", "missing_figure", "todo_check", "content_too_short", "no_options") for f in flags) else "ok",
            })
    return records


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG_OUT.mkdir(exist_ok=True)
    allrec = []
    for p in sorted((SRC / "chapters").glob("*-generated.tex")):
        allrec += parse_chapter(p)
    copied = 0
    for r in allrec:
        for f in r["figures"]:
            src = SRC / "assets/figures" / f
            if src.exists() and not (FIG_OUT / f).exists():
                shutil.copy2(src, FIG_OUT / f); copied += 1
            elif not src.exists():
                r["flags"].append("figure_file_missing:" + f); r["status"] = "review"
    with open(OUT / "questions.jsonl", "w", encoding="utf8") as f:
        for r in allrec:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print("records:", len(allrec), "ok:", sum(r["status"] == "ok" for r in allrec), "review:", sum(r["status"] == "review" for r in allrec), "figures copied:", copied)
    print("by type:", Counter(r["qtype"] for r in allrec))
    print("flags:", Counter(fl.split(":")[0] for r in allrec for fl in r["flags"]))


if __name__ == "__main__":
    main()
