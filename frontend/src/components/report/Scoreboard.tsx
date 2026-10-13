import dayjs from 'dayjs';
import type { ReportMode, StudentReport } from '@/api/types';

interface Props {
  report: StudentReport;
  mode: ReportMode;
  onPractice: (sectionId: number) => void;
}

/** 星形印章顶点：n 个尖角，外半径 R、内半径 r，viewBox 0 0 100 100 */
function starPoints(n: number, R: number, r: number) {
  const pts: string[] = [];
  for (let i = 0; i < n * 2; i++) {
    const a = (Math.PI * i) / n - Math.PI / 2;
    const rad = i % 2 ? r : R;
    pts.push(`${(50 + rad * Math.cos(a)).toFixed(2)},${(50 + rad * Math.sin(a)).toFixed(2)}`);
  }
  return pts.join(' ');
}
const STAR = starPoints(18, 49, 43);

/**
 * 战报：红框三栏黄底。左栏数量，中栏缎带 + 正确率印章，右栏最稳 / 最该回头看的知识点。
 * 只展示接口里有的数字，不推断进步幅度。
 */
export default function Scoreboard({ report: r, mode, onPractice }: Props) {
  const rate = r.answered_count ? Math.round((r.correct_count / r.answered_count) * 100) : null;
  const sorted = [...r.knowledge_points].sort((a, b) => b.mastery_level - a.mastery_level);
  const best = sorted[0];
  const weakest = sorted.length > 1 ? sorted[sorted.length - 1] : undefined;
  const pct = (v: number) => Math.round(v * 100);
  const range = mode === 'recent'
    ? `${dayjs(r.range_start).format('MM.DD')} — ${dayjs(r.range_end).format('MM.DD')}`
    : `截至 ${dayjs(r.range_end).format('YYYY.MM.DD')}`;

  return (
    <section className="scoreboard" data-reveal>
      <div className="sb-panel sb-stats">
        <div className="sb-cap">Tally · 计数</div>
        <dl>
          <div><dt>作答</dt><dd><b>{r.answered_count}</b><span>题</span></dd><small>答对 {r.correct_count}</small></div>
          <div><dt>讲题</dt><dd><b>{r.teaching_count}</b><span>道</span></dd><small>一题一会话</small></div>
          <div><dt>练习</dt><dd><b>{r.practice_count}</b><span>组</span></dd><small>计时与不计时合计</small></div>
        </dl>
      </div>

      <div className="sb-panel sb-center">
        <div className="sb-rays" aria-hidden="true" />
        <svg className="sb-ribbon" viewBox="0 0 360 124" aria-hidden="true">
          <path className="tail" d="M6 78 L44 64 L50 104 L12 118 L24 96 Z" />
          <path className="tail" d="M354 78 L316 64 L310 104 L348 118 L336 96 Z" />
          <path className="fold" d="M44 64 L50 104 L60 98 Z" />
          <path className="fold" d="M316 64 L310 104 L300 98 Z" />
          <path className="band" d="M40 66 Q180 0 320 66 L312 102 Q180 40 48 102 Z" />
          <path id="sb-arc" d="M46 88 Q180 24 314 88" fill="none" />
          <text><textPath href="#sb-arc" startOffset="50%" textAnchor="middle">{mode === 'recent' ? 'WEEK IN 4A' : 'ALL TIME'}</textPath></text>
        </svg>
        <div className="sb-title">{mode === 'recent' ? '本周战报' : '全部战报'}</div>
        <div className="sb-range">{range}</div>
        <div className="sb-seal">
          <svg viewBox="0 0 100 100" aria-hidden="true"><polygon points={STAR} /></svg>
          <div>
            <b>{rate == null ? '—' : rate}<i>{rate == null ? '' : '%'}</i></b>
            <span>正确率</span>
          </div>
        </div>
      </div>

      <div className="sb-panel sb-points">
        <div className="sb-cap">Whiteboard · 知识点</div>
        {best ? (
          <>
            <div className="sb-kp">
              <span className="sticker good">最稳</span>
              <b>{best.section_title}</b>
              <em>{pct(best.mastery_level)}<i>%</i></em>
            </div>
            {weakest && (
              <div className="sb-kp">
                <span className="sticker warn">回头看</span>
                <b>{weakest.section_title}</b>
                <em>{pct(weakest.mastery_level)}<i>%</i></em>
                <button type="button" className="sb-go" onClick={() => onPractice(weakest.section_id)}>去练这一节 →</button>
              </div>
            )}
          </>
        ) : (
          <p className="sb-empty">还没有知识点记录。做完第一组练习，这里会出现最稳和最该回头看的一节。</p>
        )}
      </div>
    </section>
  );
}
