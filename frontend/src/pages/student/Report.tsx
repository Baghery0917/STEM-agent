import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { getStudentEvaluation, getStudentReport } from '@/api/reports';
import type { ReportMode } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import TopBar from '@/components/shell/TopBar';
import { emotionBarHeight, emotionTone } from '@/utils/emotion';
import { shortTime } from '@/utils/time';
import ChapterHero from '@/components/theme/ChapterHero';
import SceneSection from '@/components/theme/SceneSection';
import PersonaCallout from '@/components/theme/PersonaCallout';

const WEEKDAY = ['日', '一', '二', '三', '四', '五', '六'];

export default function Report() {
  const student = useStudentStore((s) => s.current)!;
  const navigate = useNavigate();
  const [mode, setMode] = useState<ReportMode>('recent');
  const q = useQuery({
    queryKey: ['student-report', student.id, mode],
    queryFn: () => getStudentReport(student.id, mode, true),
    staleTime: 60_000,
  });
  const evaluation = useMutation({ mutationFn: () => getStudentEvaluation(student.id) });
  const ev = evaluation.data;
  const r = q.data;
  const rangeText = r
    ? mode === 'recent'
      ? `近 7 天 · ${dayjs(r.range_start).format('M 月 D 日')} – ${dayjs(r.range_end).format('M 月 D 日')}`
      : `全部 · 截至 ${dayjs(r.range_end).format('M 月 D 日')}`
    : '';
  const active = r?.knowledge_points.filter((k) => k.recent_practice_count + k.recent_teaching_count > 0).length ?? 0;
  const lowDays = r?.emotion_days.filter((d) => d.value != null && d.value >= 3) ?? [];

  return (
    <>
      <TopBar crumb="学习报告" showSeg={false} back />
      <section className="stage">
        <div className="report">
          <ChapterHero
            chapter="03"
            eyebrow="Apartment weekly log"
            title={<>这周在 4A，<br />你留下了什么？</>}
            description={rangeText || '正在翻阅这段时间的学习记录…'}
            showToday
            art={`${import.meta.env.BASE_URL}tbbt/apartment/leonard-bedroom-render.jpg`}
            artAlt="Apartment 4A 房间场景"
            actions={
              <>
              <div className="radio">
                <button type="button" className={mode === 'recent' ? 'on' : ''} onClick={() => setMode('recent')}>近一周</button>
                <button type="button" className={mode === 'all' ? 'on' : ''} onClick={() => setMode('all')}>全部</button>
              </div>
              <button type="button" className="btn" onClick={() => window.print()}>导出 PDF</button>
              </>
            }
          />

          {q.isLoading && <div className="empty-note">正在生成报告…</div>}
          {q.isError && <div className="empty-note">报告加载失败：{(q.error as Error).message}</div>}

          {r && (
            <>
              <div className="report-dispatch" style={{ backgroundImage: `url(${import.meta.env.BASE_URL}tbbt/backgrounds/starfield.jpg)` }}>
                <PersonaCallout
                  persona={student.persona}
                  dark
                  label="Tonight's transmission"
                  action={(
                    <button type="button" className="btn" disabled={evaluation.isPending} onClick={() => evaluation.mutate()}>
                      {evaluation.isPending ? '评价处生成中…' : ev ? '再要一份评价' : '让评价处点评'}
                    </button>
                  )}
                >
                  {r.summary
                    ?? (r.practice_count + r.teaching_count === 0
                      ? '这段时间还没有学习记录。发一道题，或者开始一组练习，报告就会有内容了。'
                      : `这段时间你练了 ${r.answered_count} 题（对 ${r.correct_count}）、讲了 ${r.teaching_count} 道。`)}
                </PersonaCallout>
              </div>

              {(ev || evaluation.isError) && (
                <SceneSection number="03.A" eyebrow="The review office" title="评价处来信" aside="外部评价服务 · 只传学号">
                    {evaluation.isError && <div className="empty-note">请求失败：{(evaluation.error as Error).message}</div>}
                    {ev?.source === 'unavailable' && (
                      <div className="empty-note">评价处暂不可用{ev.detail ? `：${ev.detail}` : ''}</div>
                    )}
                    {ev?.source === 'mcp' && (
                      <>
                        <p style={{ margin: 0, lineHeight: 1.7 }}>{ev.evaluation}</p>
                        {ev.highlights.length > 0 && (
                          <div className="tags" style={{ marginTop: 10 }}>
                            {ev.highlights.map((h) => <span key={h} className="tg on">{h}</span>)}
                          </div>
                        )}
                      </>
                    )}
                </SceneSection>
              )}

              <div className="report-flow">
                <SceneSection number="03.1" eyebrow="Whiteboard evidence" title="知识点掌握度" aside={`活跃 ${active} 个 · 点薄弱项直接练习`}>
                    {r.knowledge_points.length === 0 && <div className="empty-note">还没有知识点数据</div>}
                    {r.knowledge_points.map((k) => {
                      const pct = Math.round(k.mastery_level * 100);
                      const low = pct < 60;
                      return (
                        <button
                          type="button"
                          className="mrow"
                          key={k.section_id}
                          onClick={() => navigate('/practice/new', { state: { preselect: [k.section_id] } })}
                          title={`练习 ${k.section_title}`}
                        >
                          <div>
                            {k.section_title}
                            <div className="sub">
                              练 {mode === 'recent' ? k.recent_practice_count : k.total_practice_count} · 讲 {mode === 'recent' ? k.recent_teaching_count : k.total_teaching_count}
                              {k.total_practice_count > 0 && ` · 正确率 ${Math.round((k.correct_count / k.total_practice_count) * 100)}%`}
                            </div>
                          </div>
                          <div className="bar"><i className={low ? 'low' : ''} style={{ width: `${pct}%` }} /></div>
                          <div className="pct">{pct}%</div>
                        </button>
                      );
                    })}
                </SceneSection>

                <div className="report-side">
                  <SceneSection number="03.2" eyebrow="Room temperature" title="学习状态" aside="来自情绪识别 · 近 7 天">
                      <div className="spark">
                        {r.emotion_days.map((d) => (
                          <i
                            key={d.date}
                            className={d.value == null ? 'none' : emotionTone(d.value) === 'warn' ? 'w' : ''}
                            style={{ ['--h' as string]: `${emotionBarHeight(d.value)}%` }}
                            title={d.value == null ? `${d.date} 无记录` : `${d.date} · ${d.count} 条`}
                          />
                        ))}
                      </div>
                      <div className="axis">{r.emotion_days.map((d) => <span key={d.date}>{WEEKDAY[dayjs(d.date).day()]}</span>)}</div>
                      <div className="hint" style={{ marginTop: 8 }}>
                        {r.emotion_logs.length === 0
                          ? '开启情绪识别后，这里会显示每天的学习状态。'
                          : lowDays.length
                            ? `${lowDays.map((d) => `周${WEEKDAY[dayjs(d.date).day()]}`).join('、')}状态偏低，其余时间平稳。`
                            : '这段时间状态整体平稳。'}
                      </div>
                  </SceneSection>
                  <SceneSection number="03.3" eyebrow="Door log" title="最近记录">
                    <div className="logs">
                      {r.emotion_logs.length === 0 && <div className="empty-note">暂无记录</div>}
                      {r.emotion_logs.slice(0, 8).map((l, i) => (
                        <div key={i}>
                          <span className={`badge ${l.mode === 'teaching' ? 't' : 'p'}`}>{l.mode === 'teaching' ? '讲' : '练'}</span>
                          {l.section_title}
                          <span className={`badge ${emotionTone(l.emotion_value) === 'warn' ? 'w' : l.emotion_value <= 1.5 ? 'p' : 'g'}`}>{l.emotion}</span>
                          <span className="tm">{shortTime(l.created_at)}</span>
                        </div>
                      ))}
                    </div>
                  </SceneSection>
                </div>
              </div>
            </>
          )}
        </div>
      </section>
    </>
  );
}
