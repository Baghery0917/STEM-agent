import type { QuestionPublicResponse, SubmitAnswerResponse } from '@/api/types';
import { DIFFICULTY_LABEL, QUESTION_TYPE_LABEL } from '@/utils/enums';

export interface Choice { prefix: string; label: string }

export function parseChoices(content: string): Choice[] {
  const lines = content.split(/\n+/).map((l) => l.trim()).filter(Boolean);
  const choiceLines = lines.filter((l) => /^[A-Z][\.．、:：\s]/.test(l));
  if (choiceLines.length < 2) return [];
  return choiceLines.map((line) => ({
    prefix: line.charAt(0),
    label: line.slice(1).replace(/^[\.．、:：\s]+/, '').trim(),
  }));
}

export function parseBody(content: string): string {
  const out: string[] = [];
  for (const line of content.split(/\n/)) {
    if (/^[A-Z][\.．、:：\s]/.test(line.trim())) break;
    out.push(line);
  }
  return out.join('\n').trim();
}

export type ItemState =
  | { kind: 'pending' }
  | { kind: 'answered'; answer: string; feedback: SubmitAnswerResponse }
  | { kind: 'skipped' };

interface Props {
  index: number;
  total: number;
  question: QuestionPublicResponse;
  sectionTitle?: string;
  state: ItemState;
  draft: string;
  onDraft: (v: string) => void;
  starred: boolean;
  timed: boolean;
  onStar: () => void;
  onAsk: () => void;
  onPrev?: () => void;
  onNext?: () => void;
  onSubmit: () => void;
  onSkip: () => void;
  busy?: boolean;
}

export default function QuestionCard({
  index, total, question, sectionTitle, state, draft, onDraft, starred, timed,
  onStar, onAsk, onPrev, onNext, onSubmit, onSkip, busy,
}: Props) {
  const choices = parseChoices(question.content);
  const body = parseBody(question.content) || question.content;
  const locked = state.kind !== 'pending';
  const isSingle = question.type === 'single_choice' && choices.length >= 2;
  const isMulti = question.type === 'multiple_choice' && choices.length >= 2;
  const correct = state.kind === 'answered' ? state.feedback.correct_answer : '';
  const correctSet = new Set(correct.toUpperCase().match(/[A-Z]/g) ?? []);
  const selected = new Set((isMulti ? draft : state.kind === 'answered' ? state.answer : draft).toUpperCase().match(/[A-Z]/g) ?? []);

  const pickSingle = (p: string) => !locked && onDraft(p);
  const pickMulti = (p: string) => {
    if (locked) return;
    const next = new Set(selected);
    next.has(p) ? next.delete(p) : next.add(p);
    onDraft([...next].sort().join(''));
  };

  return (
    <div className="qcard">
      <div className="qh">
        <span className="num">第 {index + 1} 题</span>
        <span className="badge g">{QUESTION_TYPE_LABEL[question.type]}</span>
        <span className="badge g">{DIFFICULTY_LABEL[question.difficulty]}</span>
        {sectionTitle && <span>{sectionTitle}</span>}
        {timed ? (
          <button type="button" className={`ask star ${starred ? 'on' : ''}`} onClick={onStar} title="计时中不能提问，先星标，做完再问">
            <span>{starred ? '★' : '☆'}</span>{starred ? '已星标' : '星标'}
          </button>
        ) : (
          <button type="button" className="ask" onClick={onAsk} title="把这道题连同你的作答发到教学模式的新会话">
            <span>✦</span>问这道题
          </button>
        )}
      </div>
      <div className="qb">
        <div className="stem">
          {body}
          {question.content_image && <img src={question.content_image} alt="题目图片" />}
        </div>

        {(isSingle || isMulti) ? (
          <div className="opts">
            {choices.map((c) => {
              let cls = '';
              if (state.kind === 'answered') {
                if (correctSet.has(c.prefix)) cls = 'right';
                else if (selected.has(c.prefix)) cls = 'wrong';
              } else if (selected.has(c.prefix)) cls = 'pick';
              return (
                <button
                  type="button"
                  key={c.prefix}
                  className={`opt ${cls}`}
                  disabled={locked}
                  onClick={() => (isSingle ? pickSingle(c.prefix) : pickMulti(c.prefix))}
                >
                  <span className="l">{c.prefix}</span>{c.label}
                </button>
              );
            })}
          </div>
        ) : question.type === 'fill_blank' ? (
          <div className="answer">
            <label className="fill">
              答案：
              <input
                value={state.kind === 'answered' ? state.answer : draft}
                disabled={locked}
                onChange={(e) => onDraft(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !locked && onSubmit()}
                placeholder="填入答案"
              />
            </label>
          </div>
        ) : (
          <div className="answer">
            <textarea
              className="ta"
              value={state.kind === 'answered' ? state.answer : draft}
              disabled={locked}
              onChange={(e) => onDraft(e.target.value)}
              placeholder="写下你的答案或解题过程"
            />
          </div>
        )}

        {state.kind === 'answered' && (
          <div className="fb2">
            <div className={`fb ${state.feedback.is_correct ? 'ok' : 'no'}`}>
              <div className="ic">{state.feedback.is_correct ? '✓' : '✕'}</div>
              <div>
                <b>{state.feedback.is_correct ? '回答正确' : '回答错误'}</b>
                <div className="why">
                  你的答案：{state.answer || '（空）'}　·　正确答案：<b>{state.feedback.correct_answer}</b>
                </div>
              </div>
            </div>
            {state.feedback.analysis && (
              <div className="sol"><b>解析</b>　{state.feedback.analysis}</div>
            )}
            {state.feedback.analysis_image && (
              <img src={state.feedback.analysis_image} alt="解析图片" style={{ maxWidth: '100%', borderRadius: 8, marginTop: 8 }} />
            )}
          </div>
        )}
        {state.kind === 'skipped' && (
          <div className="fb2">
            <div className="fb skip">
              <div className="ic">跳</div>
              <div><b>已跳过</b><div className="why">计 0 分，不计入掌握度。做完后仍可以问这道题。</div></div>
            </div>
          </div>
        )}
      </div>
      <div className="qnav">
        <button type="button" className="btn" disabled={!onPrev} onClick={onPrev}>‹ 上一题</button>
        <span className="hintk">
          {(isSingle || isMulti) ? <>按 <kbd>A</kbd>–<kbd>D</kbd> 选择 · </> : null}
          <kbd>↵</kbd> 提交 · <kbd>←</kbd><kbd>→</kbd> 切题
        </span>
        <span className="sp" />
        {!locked && <button type="button" className="btn ghost" disabled={busy} onClick={onSkip} title="跳过计 0 分">跳过</button>}
        {!locked && <button type="button" className="btn pri" disabled={busy || !draft.trim()} onClick={onSubmit}>提交答案</button>}
        <button type="button" className="btn" disabled={!onNext} onClick={onNext}>
          {index + 1 === total ? '查看总结 ›' : '下一题 ›'}
        </button>
      </div>
    </div>
  );
}
