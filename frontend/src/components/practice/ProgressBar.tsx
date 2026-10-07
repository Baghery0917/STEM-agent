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

/** 练习顶栏：电梯楼层指示板。左边秒表，中间楼层灯，右边计数。 */
export default function ProgressBar({
  timed, index, total, states, starred, questionIds, correct, wrong, skipped, elapsedSec, revealed, onJump, onEnd,
}: Props) {
  const done = states.filter((s) => s.kind !== 'pending').length;
  return (
    <div className="ptop">
      <div className={`panel ${timed ? 'timed' : ''}`}>
        <div className="clock" title={timed ? 'Bernadette is watching' : '不计时'}>
          {timed && <PersonaAvatar persona="bernadette" size={22} />}
          <span className="digits">{timed ? fmtClock(elapsedSec) : '--:--'}</span>
          <span className="lbl">{timed ? '计时' : '不计时'}</span>
        </div>

        <div className="floors" role="tablist" aria-label="题目">
          {states.map((s, i) => {
            const cls = [
              'floor',
              s.kind === 'answered' ? (revealed && s.feedback.is_correct != null ? (s.feedback.is_correct ? 'ok' : 'no') : 'done') : s.kind === 'skipped' ? 'skip' : '',
              i === index ? 'cur' : '',
              starred.has(questionIds[i]) ? 'star' : '',
            ].join(' ');
            return (
              <button type="button" key={i} className={cls} title={`第 ${i + 1} 题`} onClick={() => onJump(i)}>
                <span className="lamp" /><span className="num">{i + 1}</span>
              </button>
            );
          })}
        </div>

        <div className="tally">
          <span className="pos"><b>{index + 1}</b><i>/ {total}</i></span>
          {revealed ? (
            <>
              <span className="chip ok" title="答对">{correct}</span>
              <span className="chip no" title="答错">{wrong}</span>
              <span className="chip skip" title="跳过">{skipped}</span>
            </>
          ) : (
            <>
              <span className="chip done" title="已答">{done - skipped}</span>
              <span className="chip skip" title="跳过">{skipped}</span>
            </>
          )}
          <button type="button" className="btn ghost sm" onClick={onEnd}>结束</button>
        </div>
      </div>
    </div>
  );
}
