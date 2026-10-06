import { fmtClock } from '@/utils/time';
import type { ItemState } from './QuestionCard';

interface Props {
  timed: boolean;
  index: number;
  total: number;
  states: ItemState[];
  starred: Set<number>;
  questionIds: number[];
  correct: number;
  wrong: number;
  skipped: number;
  elapsedSec: number;
  onJump: (i: number) => void;
  onEnd: () => void;
}

export default function ProgressBar({
  timed, index, total, states, starred, questionIds, correct, wrong, skipped, elapsedSec, onJump, onEnd,
}: Props) {
  return (
    <div className="ptop">
      <div className="pbar2">
        <span className={`badge ${timed ? 'p' : 'g'}`}>{timed ? '计时' : '不计时'}</span>
        <span>第 <span className="n">{index + 1}</span> / {total} 题</span>
        <div className="dots">
          {states.map((s, i) => {
            const cls = [
              s.kind === 'answered' ? (s.feedback.is_correct ? 'ok' : 'no') : s.kind === 'skipped' ? 'skip' : '',
              i === index ? 'cur' : '',
              starred.has(questionIds[i]) ? 'star' : '',
            ].join(' ');
            return <button type="button" key={i} className={cls} title={`第 ${i + 1} 题`} onClick={() => onJump(i)} />;
          })}
        </div>
        <span>对 <span className="n">{correct}</span> · 错 <span className="n">{wrong}</span> · 跳 <span className="n">{skipped}</span></span>
        <span className={`timer ${timed ? '' : 'off'}`}>{timed ? fmtClock(elapsedSec) : '—'}</span>
        <button type="button" className="btn ghost sm" onClick={onEnd}>结束练习</button>
      </div>
    </div>
  );
}
