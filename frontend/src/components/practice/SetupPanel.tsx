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
  /** 内嵌在页面布局里，而不是吸底 */
  inline?: boolean;
}

const COUNT_PRESETS = [5, 10, 20];

/**
 * 底部练习参数面板。
 * 规则：计时 → 做完统一批改（不可选即时反馈）；不计时 → 可选即时 / 统一。
 */
export default function SetupPanel({ studentId, suggested, preselect, loading, onStart, inline }: Props) {
  const tree = useKnowledgeTree();
  const [selected, setSelected] = useState<Set<number>>(new Set(preselect ?? []));
  const [treeOpen, setTreeOpen] = useState(false);
  const [count, setCount] = useState(10);
  const [custom, setCustom] = useState(false);
  const [difficulty, setDifficulty] = useState<Set<Difficulty>>(new Set(['easy', 'medium']));
  const [types, setTypes] = useState<Set<QuestionType>>(new Set(['single_choice', 'multiple_choice', 'fill_blank']));
  const [timed, setTimed] = useState(true);
  const [instant, setInstant] = useState(true);

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
    if (n.has(v)) n.delete(v); else n.add(v);
    setter(n);
  };

  const suggestedIds = new Set(suggested.map((s) => s.section_id));
  const extraSelected = ids.filter((id) => !suggestedIds.has(id));
  const canStart = ids.length > 0 && difficulty.size > 0 && types.size > 0 && (matched ?? 1) > 0 && !loading;
  const instantEffective = timed ? false : instant;

  let summary: string;
  if (ids.length === 0) summary = '先选一个范围';
  else if (match.isFetching) summary = '匹配中…';
  else if (matched == null) summary = '';
  else if (matched === 0) summary = '题库里没有符合条件的题';
  else summary = `题库匹配 ${matched} 题 · 本次出 ${effective} 题${timed ? ` · 预计 ${Math.max(1, Math.round(effective * 1.2))} 分钟` : ''}`;

  return (
    <div className={inline ? 'setup-inline' : 'composer-wrap'}>
      <div className={inline ? '' : 'composer wide'}>
        <div className="setup-panel">
          <div className="sh">
            练习参数
            <span className="sp">范围按薄弱点预选，可改</span>
          </div>

          <div className="sp-row">
            <div className="sp-lbl">范围</div>
            <div className="sp-body">
              <div className="tags">
                {suggested.map((s) => (
                  <button type="button" key={s.section_id} className={`tg ${selected.has(s.section_id) ? 'on' : ''}`} onClick={() => toggle(selected, s.section_id, setSelected)}>
                    {s.title}<span className="m">{Math.round(s.mastery * 100)}%</span>
                  </button>
                ))}
                {extraSelected.map((id) => (
                  <button type="button" key={id} className="tg on" onClick={() => toggle(selected, id, setSelected)}>
                    {tree.data?.sectionById.get(id)?.title ?? `#${id}`}<span className="m">×</span>
                  </button>
                ))}
                <button type="button" className={`tg add ${treeOpen ? 'on' : ''}`} onClick={() => setTreeOpen((v) => !v)}>
                  {treeOpen ? '收起' : '＋ 从知识树选'}
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

          <div className="sp-grid">
            <div className="sp-row">
              <div className="sp-lbl">题数</div>
              <div className="sp-body">
                <div className="radio">
                  {COUNT_PRESETS.map((n) => (
                    <button type="button" key={n} className={!custom && count === n ? 'on' : ''} onClick={() => { setCustom(false); setCount(n); }}>{n}</button>
                  ))}
                  <button type="button" className={custom ? 'on' : ''} onClick={() => setCustom(true)}>自定义</button>
                </div>
                {custom && (
                  <input
                    className="num"
                    type="number"
                    min={1}
                    max={100}
                    value={count}
                    onChange={(e) => setCount(Math.max(1, Math.min(100, Number(e.target.value) || 1)))}
                  />
                )}
              </div>
            </div>
            <div className="sp-row">
              <div className="sp-lbl">难度</div>
              <div className="sp-body">
                <div className="tags">
                  {DIFFICULTY_OPTIONS.map((d) => (
                    <button type="button" key={d.value} className={`tg ${difficulty.has(d.value) ? 'on' : ''}`} onClick={() => toggle(difficulty, d.value, setDifficulty)}>{d.label}</button>
                  ))}
                </div>
              </div>
            </div>
            <div className="sp-row">
              <div className="sp-lbl">题型</div>
              <div className="sp-body">
                <div className="tags">
                  {QUESTION_TYPE_OPTIONS.map((t) => (
                    <button type="button" key={t.value} className={`tg ${types.has(t.value) ? 'on' : ''}`} onClick={() => toggle(types, t.value, setTypes)}>{t.label}</button>
                  ))}
                </div>
              </div>
            </div>
            <div className="sp-row">
              <div className="sp-lbl">节奏</div>
              <div className="sp-body">
                <div className="radio">
                  <button type="button" className={timed ? 'on' : ''} onClick={() => setTimed(true)}>计时</button>
                  <button type="button" className={!timed ? 'on' : ''} onClick={() => setTimed(false)}>不计时</button>
                </div>
                <div className="radio" aria-label="批改方式">
                  <button type="button" className={instantEffective ? 'on' : ''} disabled={timed} onClick={() => setInstant(true)}>每题即时反馈</button>
                  <button type="button" className={!instantEffective ? 'on' : ''} onClick={() => setInstant(false)}>做完统一批改</button>
                </div>
                <div className="hint">
                  {timed ? '计时练习做完统一批改，中途不能提问，卡住先星标' : instant ? '每题提交后立刻看答案，任何一题都可转去提问' : '做完一起看答案，任何一题都可转去提问'}
                </div>
              </div>
            </div>
          </div>

          <div className="sf">
            <span className="sum">{summary}</span>
            <button
              type="button"
              className="btn acc"
              disabled={!canStart}
              onClick={() => onStart({
                student_id: studentId,
                knowledge_point_ids: ids,
                difficulty_range: [...difficulty],
                question_types: [...types],
                total_count: count,
                timed,
                instant_feedback: instantEffective,
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
