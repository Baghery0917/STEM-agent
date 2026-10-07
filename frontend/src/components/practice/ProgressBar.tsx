import { fmtClock } from '@/utils/time';
import type { ItemState } from './QuestionCard';
import PersonaAvatar from '@/components/theme/PersonaAvatar';

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

/** 练习右侧：一部电梯。顶上秒表，中间楼层灯自下而上（1F 在底），底下计数。 */
export default function ProgressBar({
  timed, index, total, states, starred, questionIds, correct, wrong, skipped, elapsedSec, revealed, onJump, onEnd,
}: Props) {
  const done = states.filter((s) => s.kind !== 'pending').length;
  const floors = states.map((s, i) => ({ s, i })).reverse();
  return (
    <aside className={`elevator ${timed ? 'timed' : ''}`}>
      <div className="clock" title={timed ? 'Bernadette is watching' : '不计时'}>
        {timed && <PersonaAvatar persona="bernadette" size={24} />}
        <span className="digits">{timed ? fmtClock(elapsedSec) : '--:--'}</span>
        <span className="lbl">{timed ? '计时中' : '不计时'}</span>
      </div>

      <div className="shaft" role="tablist" aria-label="题目">
        {floors.map(({ s, i }) => {
          const cls = [
            'floor',
            s.kind === 'answered' ? (revealed && s.feedback.is_correct != null ? (s.feedback.is_correct ? 'ok' : 'no') : 'done') : s.kind === 'skipped' ? 'skip' : '',
            i === index ? 'cur' : '',
            starred.has(questionIds[i]) ? 'star' : '',
          ].join(' ');
          return (
            <button type="button" key={i} className={cls} title={`第 ${i + 1} 题`} onClick={() => onJump(i)}>
              <span className="num">{i + 1}</span>
              <span className="lamp" />
            </button>
          );
        })}
        <span className="car" style={{ ['--pos' as string]: total - 1 - index }} aria-hidden="true" />
      </div>

      <div className="tally">
        <div className="pos"><b>{index + 1}</b><i>/ {total}</i></div>
        {revealed ? (
          <div className="chips">
            <span className="chip ok" title="答对">{correct}</span>
            <span className="chip no" title="答错">{wrong}</span>
            <span className="chip skip" title="跳过">{skipped}</span>
          </div>
        ) : (
          <div className="chips">
            <span className="chip done" title="已答">{done - skipped}</span>
            <span className="chip skip" title="跳过">{skipped}</span>
          </div>
        )}
        <button type="button" className="btn ghost sm" onClick={onEnd}>结束</button>
      </div>
    </aside>
  );
}
