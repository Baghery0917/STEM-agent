import { useState } from 'react';
import type { PipelineStatus, TeachingMessageResponse } from '@/api/types';

type StageKey = 'llm_analysis' | 'student_data' | 'strategy' | 'reference_search';

const STAGES: { key: StageKey; label: string }[] = [
  { key: 'llm_analysis', label: '知识点分析' },
  { key: 'student_data', label: '读取你的画像' },
  { key: 'strategy', label: '教学策略' },
  { key: 'reference_search', label: '检索参考题' },
];

interface Props {
  pipelineStatus: PipelineStatus;
  /** 这一轮之前（含）的系统消息 */
  messages: TeachingMessageResponse[];
  /** 首轮流水线：true；后续追问只有 strategy 一步 */
  firstRound: boolean;
  startedAt?: string | null;
  finishedAt?: string | null;
}

/** 流水线进度以可折叠"思考块"的形式放在 AI 回复里 */
export default function AgentTrace({ pipelineStatus, messages, firstRound, startedAt, finishedAt }: Props) {
  const stages = firstRound ? STAGES : STAGES.filter((s) => s.key === 'strategy');
  const byType = new Map(messages.map((m) => [m.message_type, m] as const));
  const running = firstRound && (pipelineStatus === 'pending' || pipelineStatus === 'running');
  const failed = firstRound && pipelineStatus === 'failed';
  const firstPending = stages.findIndex((s) => !byType.has(s.key));
  const [open, setOpen] = useState(firstRound);

  let elapsed: string | null = null;
  if (startedAt && finishedAt) {
    const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime();
    if (ms > 0) elapsed = `${(ms / 1000).toFixed(1)}s`;
  }

  return (
    <details className="trace" open={open || running || failed} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary>
        {running ? <span className="spin" /> : failed ? <span className="fail">!</span> : <span className="ok">✓</span>}
        {running ? '正在分析' : failed ? '分析中断，已给出兜底回复' : `分析完成${elapsed ? ` · 用时 ${elapsed}` : ''}`}
        <span className="chev">›</span>
      </summary>
      <div className="steps">
        {stages.map((s, idx) => {
          const msg = byType.get(s.key);
          const cls = msg ? 'done' : failed && idx === firstPending ? 'fail' : running && idx === firstPending ? 'run' : '';
          return (
            <div key={s.key} className={`step ${cls}`}>
              <span className="st" />
              <span className="nm">{s.label}</span>
              <span className="out">{msg ? renderOut(s.key, msg.content) : cls === 'run' ? '请求中…' : ''}</span>
            </div>
          );
        })}
      </div>
    </details>
  );
}

function renderOut(key: StageKey, content: string) {
  if (key === 'llm_analysis') {
    const names = Array.from(content.matchAll(/- \d+: (.+)/g)).map((m) => m[1].trim());
    if (names.length) return names.map((n) => <span key={n} className="pill">{n}</span>);
    return content.startsWith('No knowledge') ? '未识别到知识点' : content;
  }
  if (key === 'strategy') {
    const m = content.match(/Strategy:\s*(.+)/);
    return m ? m[1].trim() : content;
  }
  if (key === 'reference_search') {
    const hits = Array.from(content.matchAll(/#(\d+)[^\d]*?(\d+(?:\.\d+)?)%/g));
    if (hits.length) return `命中 ${hits.length} 道相似题 · ${hits.map((h) => `#${h[1]}（${h[2]}%）`).join(' ')}`;
    if (/^No reference/i.test(content)) return '未找到足够相似的题';
    return content.split('\n')[0];
  }
  // student_data：取前两行
  return content.split('\n').filter(Boolean).slice(0, 2).join(' · ');
}
