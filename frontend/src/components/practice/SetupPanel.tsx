import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { Difficulty, QuestionType, StartPracticeRequest } from '@/api/types';
import { matchPractice } from '@/api/practice';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import { DIFFICULTY_OPTIONS, QUESTION_TYPE_OPTIONS } from '@/utils/enums';

interface Props {
  studentId: number;
  /** 建议预选的知识点（来自报告的薄弱点），带掌握度 */
  suggested: { section_id: number; title: string; mastery: number }[];
  preselect?: number[];
  loading?: boolean;
  onStart: (body: StartPracticeRequest) => void;
}

const COUNT_PRESETS = [5, 10, 20];

export default function SetupPanel({ studentId, suggested, preselect, loading, onStart }: Props) {
  const tree = useKnowledgeTree();
  const [selected, setSelected] = useState<Set<number>>(new Set(preselect ?? []));
  const [treeOpen, setTreeOpen] = useState(false);
  const [count, setCount] = useState(10);
  const [custom, setCustom] = useState(false);
  const [difficulty, setDifficulty] = useState<Set<Difficulty>>(new Set(['easy', 'medium']));
  const [types, setTypes] = useState<Set<QuestionType>>(new Set(['single_choice', 'multiple_choice', 'fill_blank']));
  const [timed, setTimed] = useState(true);

  // 默认预选薄弱点（最多两个），用户未指定时
  useEffect(() => {
    if (preselect?.length || selected.size) return;
    if (suggested.length) setSelected(new Set(suggested.slice(0, 2).map((s) => s.section_id)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [suggested.length]);

  const ids = useMemo(() => [...selected], [selected]);
  const match = useQuery({
    queryKey: ['practice-match', ids, [...difficulty], [...types]],
    queryFn: () => matchPractice({ knowledge_point_ids: ids, difficulty_range: [...difficulty], question_types: [...types] }),
    enabled: ids.length > 0 && difficulty.size > 0 && types.size > 0,
  });
  const matched = match.data?.matched_count;
  const effective = matched != null ? Math.min(count, matched) : count;

  const toggle = <T,>(set: Set<T>, v: T, setter: (s: Set<T>) => void) => {
    const n = new Set(set);
    n.has(v) ? n.delete(v) : n.add(v);
    setter(n);
  };

  const suggestedIds = new Set(suggested.map((s) => s.section_id));
  const extraSelected = ids.filter((id) => !suggestedIds.has(id));
  const canStart = ids.length > 0 && difficulty.size > 0 && types.size > 0 && (matched ?? 1) > 0 && !loading;

  return (
    <div className="composer-wrap">
      <div className="composer wide">
        <div className="setup-panel">
          <div className="sh">练习参数<span className="sp">范围按你最近的薄弱点预选，可改 · 范围即题目来源</span></div>
          <div className="sg">
            <div className="row full">
              <div className="lbl">范围</div>
              <div>
                <div className="tags">
                  {suggested.map((s) => (
                    <button type="button" key={s.section_id} className={`tg ${selected.has(s.section_id) ? 'on' : ''}`} onClick={() => toggle(selected, s.section_id, setSelected)}>
                      {s.title} <span className="m">{Math.round(s.mastery * 100)}%</span>
                    </button>
                  ))}
                  {extraSelected.map((id) => (
                    <button type="button" key={id} className="tg on" onClick={() => toggle(selected, id, setSelected)}>
                      {tree.data?.sectionById.get(id)?.title ?? `#${id}`}
                    </button>
                  ))}
                  <button type="button" className="tg add" onClick={() => setTreeOpen((v) => !v)}>
                    {treeOpen ? '收起知识树' : '＋ 从知识树选'}
                  </button>
                </div>
                {treeOpen && tree.data && (
                  <div className="treepick">
                    {tree.data.volumes.map((v) => (
                      <div key={v.id}>
                        <div className="v">{v.title}</div>
                        {(tree.data!.byVolume.get(v.id) ?? []).map((c) => (
                          <div key={c.id}>
                            <div className="c">{c.title}</div>
                            {(tree.data!.byChapter.get(c.id) ?? []).map((s) => (
                              <label key={s.id}>
                                <input type="checkbox" checked={selected.has(s.id)} onChange={() => toggle(selected, s.id, setSelected)} />
                                {s.title}
                              </label>
                            ))}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="row">
              <div className="lbl">题数</div>
              <div>
                <div className="radio">
                  {COUNT_PRESETS.map((n) => (
                    <button type="button" key={n} className={!custom && count === n ? 'on' : ''} onClick={() => { setCustom(false); setCount(n); }}>{n}</button>
                  ))}
                  <button type="button" className={custom ? 'on' : ''} onClick={() => setCustom(true)}>自定义</button>
                  {custom && <input type="number" min={1} max={100} value={count} onChange={(e) => setCount(Math.max(1, Math.min(100, Number(e.target.value) || 1)))} />}
                </div>
                <div className="hint">每题都可跳过，跳过计 0 分、不计入掌握度</div>
              </div>
            </div>
            <div className="row">
              <div className="lbl">难度</div>
              <div className="tags">
                {DIFFICULTY_OPTIONS.map((d) => (
                  <button type="button" key={d.value} className={`tg ${difficulty.has(d.value) ? 'on' : ''}`} onClick={() => toggle(difficulty, d.value, setDifficulty)}>{d.label}</button>
                ))}
              </div>
            </div>
            <div className="row">
              <div className="lbl">题型</div>
              <div className="tags">
                {QUESTION_TYPE_OPTIONS.map((t) => (
                  <button type="button" key={t.value} className={`tg ${types.has(t.value) ? 'on' : ''}`} onClick={() => toggle(types, t.value, setTypes)}>{t.label}</button>
                ))}
              </div>
            </div>
            <div className="row">
              <div className="lbl">计时</div>
              <div>
                <div className="swrow">
                  <button type="button" className={`toggle ${timed ? 'on' : ''}`} onClick={() => setTimed((v) => !v)} aria-label="每题计时" />
                  <span>每题计时</span>
                </div>
                <div className="hint">计时中不能跳去提问，只能先星标，做完再问</div>
              </div>
            </div>
            <div className="row">
              <div className="lbl">批改</div>
              <div><div className="radio"><button type="button" className="on">每题即时反馈</button></div></div>
            </div>
          </div>
          <div className="sf">
            <span className="sum">
              {ids.length === 0 ? '先选一个范围' : match.isFetching ? '匹配中…' : matched == null ? '' : matched === 0 ? '题库里没有符合条件的题' : `题库匹配 ${matched} 题 · 本次出 ${effective} 题${timed ? ` · 预计 ${Math.max(1, Math.round(effective * 1.2))} 分钟` : ''}`}
            </span>
            <button
              type="button"
              className="btn acc"
              disabled={!canStart}
              onClick={() => onStart({
                student_id: studentId, knowledge_point_ids: ids, difficulty_range: [...difficulty],
                question_types: [...types], total_count: count, timed,
              })}
            >
              {loading ? '出题中…' : '确认开始 ↵'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
