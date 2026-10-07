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
  /** 统一批改模式下结束前不显示对错颜色与计数 */
  revealed: boolean;
  onJump: (i: number) => void;
  onEnd: () => void;
}

export default function ProgressBar({
  timed, index, total, states, starred, questionIds, correct, wrong, skipped, elapsedSec, revealed, onJump, onEnd,
}: Props) {
  return (
    <div className="ptop">
      <div className="pbar2">
        <span className={`badge ${timed ? 'p' : 'g'}`}>{timed ? '计时' : '不计时'}</span>
        <span>第 <span className="n">{index + 1}</span> / {total} 题</span>
        <div className="dots">
          {states.map((s, i) => {
            const cls = [
              s.kind === 'answered' ? (revealed && s.feedback.is_correct != null ? (s.feedback.is_correct ? 'ok' : 'no') : 'done') : s.kind === 'skipped' ? 'skip' : '',
              i === index ? 'cur' : '',
              starred.has(questionIds[i]) ? 'star' : '',
            ].join(' ');
            return <button type="button" key={i} className={cls} title={`第 ${i + 1} 题`} onClick={() => onJump(i)} />;
          })}
        </div>
        {revealed
          ? <span>对 <span className="n">{correct}</span> · 错 <span className="n">{wrong}</span> · 跳 <span className="n">{skipped}</span></span>
          : <span>已答 <span className="n">{correct + wrong}</span> · 跳 <span className="n">{skipped}</span></span>}
        <span className={`timer ${timed ? '' : 'off'}`}>{timed ? fmtClock(elapsedSec) : '—'}</span>
        <button type="button" className="btn ghost sm" onClick={onEnd}>结束练习</button>
      </div>
    </div>
  );
}
