import type { PracticeItemWithQuestionResponse, PracticeSessionResponse, QuestionPublicResponse } from '@/api/types';
import { parseBody } from './QuestionCard';
import { fmtDuration } from '@/utils/time';

interface Props {
  session: PracticeSessionResponse;
  questions: QuestionPublicResponse[];
  items: PracticeItemWithQuestionResponse[];
  scope: string;
  onReview: (index: number) => void;
  onAsk: (questionIds: number[]) => void;
  onAgain: () => void;
}

export default function PracticeSummary({ session, questions, items, scope, onReview, onAsk, onAgain }: Props) {
  const byQ = new Map(items.map((i) => [i.question_id, i]));
  const answered = items.filter((i) => !i.is_skipped);
  const durations = answered.map((i) => i.duration_seconds).filter((d): d is number => d != null);
  const avg = durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : null;
  const totalSec = session.ended_at
    ? Math.max(0, Math.round((new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 1000))
    : null;
  const starredIds = session.starred_question_ids;
  const wrongIds = items.filter((i) => !i.is_skipped && !i.is_correct).map((i) => i.question_id);
  const askIds = [...new Set([...starredIds, ...wrongIds])];
  const rate = session.correct_count + session.wrong_count > 0
    ? Math.round((session.correct_count / (session.correct_count + session.wrong_count)) * 100)
    : null;

  const row = (q: QuestionPublicResponse, i: number) => {
    const it = byQ.get(q.id);
    const st = !it ? 'na' : it.is_skipped ? 'skip' : it.is_correct ? 'ok' : 'no';
    const isStar = starredIds.includes(q.id);
    return (
      <div key={q.id} className={`ql ${isStar ? 'starred' : ''}`}>
        <span className={`st ${st}`}>{st === 'skip' ? '跳' : i + 1}</span>
        <span className="t" onClick={() => onReview(i)} title="回看这道题">
          {isStar ? '★ ' : ''}{parseBody(q.content).split('\n')[0] || q.content}
          {st === 'skip' && <span className="muted"> · 跳过，计 0 分</span>}
          {st === 'na' && <span className="muted"> · 未作答</span>}
        </span>
        <span className="tm">{fmtDuration(it?.duration_seconds)}</span>
        <button type="button" className="ask" onClick={() => onAsk([q.id])}>问这题</button>
      </div>
    );
  };

  return (
    <div className="pwrap">
      <div className="qcard">
        <div className="qh">
          <span className="num">练习完成</span>
          <span className={`badge ${session.timed ? 'p' : 'g'}`}>{session.timed ? '计时' : '不计时'}</span>
          <span>{scope} · {session.total_count} 题</span>
          {totalSec != null && <span className="muted">· 共 {fmtDuration(totalSec)}</span>}
        </div>
        <div className="qb">
          <div className="stats">
            <div className="stat ok"><div className="v">{session.correct_count}</div><div className="k">正确{rate != null ? ` · ${rate}%` : ''}</div></div>
            <div className="stat no"><div className="v">{session.wrong_count}</div><div className="k">错误</div></div>
            <div className="stat"><div className="v">{session.skip_count}</div><div className="k">跳过 · 计 0 分</div></div>
            <div className="stat"><div className="v">{avg != null ? `${avg}s` : '—'}</div><div className="k">平均用时</div></div>
          </div>

          {starredIds.length > 0 && (
            <>
              <div className="grp" style={{ padding: '16px 0 6px' }}>
                星标的题 <span className="muted" style={{ fontWeight: 400, textTransform: 'none' }}>· 做题时标记的，现在可以问了</span>
              </div>
              <div className="qlist" style={{ marginTop: 0 }}>
                {questions.map((q, i) => (starredIds.includes(q.id) ? row(q, i) : null))}
              </div>
            </>
          )}

          <div className="grp" style={{ padding: '16px 0 6px' }}>全部题目</div>
          <div className="qlist" style={{ marginTop: 0 }}>{questions.map(row)}</div>
        </div>
        <div className="qnav">
          {askIds.length > 0 && (
            <button type="button" className="btn acc" onClick={() => onAsk(askIds)}>
              ✦ 把星标和错题一起发给老师讲（{askIds.length}）
            </button>
          )}
          <button type="button" className="btn" onClick={onAgain}>再来一组同参数</button>
          <span className="sp" />
          <button type="button" className="btn ghost" onClick={onAgain}>新建练习</button>
        </div>
      </div>
    </div>
  );
}
