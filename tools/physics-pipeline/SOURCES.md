# 大学物理资料来源清单

采集日期：2026-10-08。全部放在 `raw/` 下，已删除各仓库的 `.git` 与 MIT OCW 的原始 zip。

## raw/openstax/ — OpenStax University Physics 三卷（CC BY 4.0）
- 来源：https://openstax.org/subjects/science（assets.openstax.org 官方 PDF）
- 内容：Vol.1 力学/波/热，Vol.2 电磁学，Vol.3 光学/近代物理。文字版 PDF，每章末带习题（无完整解答）。
- 许可明确可再分发，是最干净的英文教材语料。

## raw/mit-ocw/ — MIT OpenCourseWare 六门课（CC BY-NC-SA）
- 8.01sc-fall-2016 经典力学（讲义 PDF、习题集、考试及解答）
- 8.01l-fall-2005 力学（4 套练习考试 + 解答 + 公式表、32 讲讲义）
- 8.02-spring-2007 电磁学（讲义、习题、考试）
- 8.02t-spring-2005 电磁学 TEAL 版
- 8.03sc-fall-2016 振动与波
- 8.04-spring-2016 量子物理 I
- 每门目录内 `static_resources/` 为 PDF，`pages/` 为 HTML 讲义，`*.vtt/*.srt` 为视频字幕。

## raw/github-cn/ — 国内高校课程共享仓库（按校）
| 目录 | 仓库 | 内容要点 |
|---|---|---|
| PHYS1001 | HITSZ-OpenAuto/PHYS1001 | 哈工大（深圳）大学物理：清华题库 10 份分章练习（有答案）、哈工大本部 2010-2026 期末/期中试卷（多数有答案）、上交 2004-2015 试卷、马文蔚《物理学》第六版习题解答、学生笔记 |
| THU-REKCARC | PKUanonym/REKCARC-TSC-UHT | 清华大学物理 B(1)/B(2)/英文班：期中期末试卷、清华题库分章 docx/pdf、讨论课题目与解答；含大量 jpg 照片版 |
| USTC-phyexam | ustcphyexam/ustcphyexam.github.io | 中科大普通物理试卷：力学/热学/电磁学/光学/原子物理 2014-2026 期中期末，文件名编码见 `_pages/JuniorPhy.md`；也含四大力学试卷 |
| SYSU-physchtest | physchtest/physchtest.github.io | 中山大学物理学院：电磁学 2017-2019 期中期末（含答案）、原子物理、量子力学、电动力学等 |
| HUST-Xuejie | SukunaShinmyoumaru-hust/Hust-opensource-Xuejie | 华中科大大学物理（一）（二）：2022-2024 期末卷、集成学院 2011-2023 试卷（含答案）、教材 PDF、习题册与答案、全套课件 |
| ZJU-icicles | qsctech/zju-icicles | 浙大大学物理：教材 21 章答案 PDF、知识点总结；普通物理学(H) 的 Instructor Solutions Manual |
| NENU-MisterHope | Mister-Hope/physics | 东北师大物理系：力学/电磁学/热学/光学/原子物理 课件 PPT、讲义 PDF、课后答案、参考书（含秦允豪《热学》习题指导、赵凯华《新概念物理》题解） |
| QLU | Peakors/QLU_FinalExamPaper | 齐鲁工业大学 19-20 学年大学物理 III A/B 卷及答案 |

## raw/latex-solutions/ — LaTeX 源码题解
- university-physics（qyxf）：大学物理作业题解析上/下册 `.tex` 源码 + 2011-2012 期末题；LaTeX 源可直接解析成结构化题目。
- HomeWork_Physics（BHanZhang）：2019-2020 普通物理作业解答 `.tex`。

## 未收录但可补的来源
- TapXWorld/ChinaTextbook：目前大学部分只有数学四门，无物理。
- B 站 / 天翼云盘上的程守洙《普通物理学》、马文蔚《物理学》扫描版：非开放许可，未拉取。
- MIT OCW 8.01 Walter Lewin 1999 版、8.02 2002 版：无打包 zip，需逐页抓。

## 清洗时需要注意的事实
- 抽样 40 个中文 PDF 中 9 个为纯扫描（无文字层），需 OCR；清华题库与科大试卷多为文字版。
- THU-REKCARC 下有 180 个 jpg 照片版试卷与 11 个 rar/zip 压缩包未解开。
- 本机无 pdftotext/mutool，Python 有 pypdf 6.19，无 PyMuPDF。

---

# 第二轮补充（2026-10-08）：成体系的知识整理

## raw/structured/ — 结构化知识源（可直接机器解析）
| 目录 | 来源 | 内容 | 格式 |
|---|---|---|---|
| openstax-cnxml-source | openstax/osbooks-university-physics-bundle | University Physics 三卷的官方源码：322 个 module，每章 `index.cnxml`（XML + MathML），三卷 `collection.xml` 给出章节树。含全部课后 exercise 标签 | CNXML/MathML |
| college-physics-a1-notes | study-png/college-physics-a1-notes | **清华大学物理试题库 LaTeX 修复版：795 题，10 章（力学/刚体/相对论/振动/波/热学/电学/磁学/光学/量子），每题 `problembox`（题干）+ `officialbox`（原题库答案）+ `analysisbox`（思路/做法/易错点）**。另含北理工大物 A1 力学、热学章节 LaTeX 笔记 | LaTeX |
| LinhoNotes | Linho1219/LinhoNotes | 大学物理速通笔记：力学 4 节、热学 2 节、相对论 2 节、电磁学 5 节，markdown + KaTeX + svg 插图，含例题 | Markdown |
| 0112-UniversityPhysics | No8ah/0112-UniversityPhysics | 东北大学大物笔记：按「章 → 节 → 概念」拆成 119 个 md 原子文件（热学第 10-11 章、电学第 12-14 章、光学第 11 章） | Markdown |
| CollegePhysics / CollegePhysicsNew | liyuxuan3003 | 大学物理 LaTeX 笔记，力学与电磁学 165 个 tex、热学与光学 123 个 tex | LaTeX |
| THU-Physics-for-Scientists-and-Engineers | tingyunaiai9 | 清华 2024 春秋《大学物理》复习笔记：电磁学、光学、量子物理三份 tex + pdf | LaTeX |
| Notes-of-Electromagnetism | An-314 | 清华物理系姜开利《电磁学》笔记 | Typst |
| Notes-on-College-Physics-Courses | ZhangtongCN | 南信大大物笔记：电流与恒磁场、电磁感应、光的干涉/衍射/偏振、早期量子论、量子力学基础，7 份 PDF | PDF |
| College-Pysics | ChenZhiFan | 大学物理 公式/知识点/作业 三类 md | Markdown |
| SMU_Normal_Physics | Water-bros | 南方医科大《大学物理》下册笔记，单文件 md 32KB | Markdown |
| Feynman-Lectures-zh-LaTeX | RockLakeGrass | 费曼物理学讲义中文 LaTeX：第一卷 52 章全、第二卷和第三卷各第 1 章 | LaTeX |

## raw/syllabus/ — 教学大纲与知识点清单（定义「体系」的骨架）
- `教育部_非物理类理工学科大学物理课程教学基本要求_2005版_摘录.md`：教指委文件正文，A 类 74 条 / B 类 51 条的模块分布与学时；附 2023 版相对 2010 版的逐条变化。
- `2023版与2010版理工科类大学物理课程教学基本要求的比较_物理与工程2024.pdf`：东南大学张勇等的比较论文，是目前网上唯一能拿到的 2023 版条目级信息（光学表 1、量子物理表 2 列出了具体条目名）。2023 版原书由高教社出版，未开放。
- `贵州理工学院_大学物理1教学大纲_2016.md`：按「知识点 → 知识 → 能力 → L1-L4 要求程度」表格化的大纲，10 章，可直接作知识点标签表。
- `河南师范大学_大学物理I教学大纲_2010.md`：12 章，每章含内容、目的与要求、重点、难点。
- `吉林大学_大学物理B教学大纲.pdf`、`兰州工业学院_基础学科部教学大纲2019.pdf`：两校大纲 PDF。

## 对「系统的知识」的判断
- **骨架**用教指委《基本要求》的模块 → A/B 类条目，这是国内所有大学物理教材和试卷共同遵循的分类，STEM-agent 的「册 → 章 → 节」可以直接映射到「模块 → 条目 → 知识点」。
- **正文**最干净的是 OpenStax CNXML（英文、带 MathML、CC BY）和 LinhoNotes / 0112-UniversityPhysics（中文 markdown，原子化程度高）。
- **题目**最干净的是清华题库 LaTeX 版 795 题，三段式结构已经和 STEM-agent 题库字段（题干、答案、解析）对齐；注意其 analysisbox 解析是仓库作者后补的，需抽检正确性。
- 没有找到现成的大学物理知识图谱数据集（json/csv 带先修关系），只有一篇 arXiv 2412.05453 用 LLM 从高中物理生成知识图谱的论文。知识图谱需要自建。
