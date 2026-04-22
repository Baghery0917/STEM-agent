import { Alert, Steps } from 'antd';
import {
  CheckCircleFilled,
  ExclamationCircleFilled,
  LoadingOutlined,
} from '@ant-design/icons';
import type { PipelineStatus, TeachingMessageResponse } from '@/api/types';

interface Props {
  pipelineStatus: PipelineStatus;
  messages: TeachingMessageResponse[];
}

type StageKey =
  | 'llm_analysis'
  | 'student_data'
  | 'strategy'
  | 'reference_search'
  | 'assistant_chat';

const STAGES: { key: StageKey; label: string }[] = [
  { key: 'llm_analysis', label: '知识点分析' },
  { key: 'student_data', label: '学生画像' },
  { key: 'strategy', label: '教学策略' },
  { key: 'reference_search', label: '参考题检索' },
  { key: 'assistant_chat', label: '生成讲解' },
];

function isStageDone(key: StageKey, messages: TeachingMessageResponse[]) {
  if (key === 'assistant_chat') {
    return messages.some(
      (m) => m.role === 'assistant' && m.message_type === 'chat',
    );
  }
  return messages.some((m) => m.message_type === key);
}

export default function PipelineProgress({ pipelineStatus, messages }: Props) {
  if (pipelineStatus === 'done') return null;

  const isFailed = pipelineStatus === 'failed';
  const doneFlags = STAGES.map((s) => isStageDone(s.key, messages));
  const currentIdx = doneFlags.findIndex((done) => !done);
  const activeIdx = currentIdx === -1 ? STAGES.length : currentIdx;

  return (
    <div
      style={{
        padding: '12px 20px',
        background: '#fff',
        borderBottom: '1px solid #f0f0f0',
      }}
    >
      <Steps
        size="small"
        current={activeIdx}
        status={isFailed ? 'error' : 'process'}
        items={STAGES.map((stage, idx) => {
          const done = doneFlags[idx];
          const isCurrent = idx === activeIdx;
          let icon: React.ReactNode;
          if (done) {
            icon = <CheckCircleFilled style={{ color: '#10b981' }} />;
          } else if (isFailed && isCurrent) {
            icon = <ExclamationCircleFilled style={{ color: '#ef4444' }} />;
          } else if (isCurrent) {
            icon = <LoadingOutlined style={{ color: '#2563eb' }} />;
          } else {
            icon = undefined;
          }
          return { title: stage.label, icon };
        })}
      />
      {isFailed && (
        <Alert
          style={{ marginTop: 8 }}
          type="error"
          showIcon
          message="讲解生成失败，已写入兜底回复。可以尝试追问或取消重开。"
        />
      )}
    </div>
  );
}
