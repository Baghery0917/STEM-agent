import { Card, Divider, Empty, Tag, Typography } from 'antd';
import type { TeachingSessionDetailResponse } from '@/api/types';

interface Props {
  session: TeachingSessionDetailResponse;
}

export default function StrategyPanel({ session }: Props) {
  const references = session.messages.flatMap((m) => m.references ?? []);
  const dedup = new Map<number, (typeof references)[number]>();
  references.forEach((r) => {
    if (!dedup.has(r.question_id)) dedup.set(r.question_id, r);
  });

  return (
    <div style={{ padding: 16, height: '100%', overflow: 'auto' }}>
      <Card size="small" title="会话信息" style={{ marginBottom: 12 }}>
        <Typography.Paragraph style={{ margin: 0 }}>
          <strong>状态：</strong>
          <Tag color={session.status === 'active' ? 'processing' : 'default'}>
            {session.status}
          </Tag>
        </Typography.Paragraph>
        <Typography.Paragraph style={{ margin: 0 }}>
          <strong>会话 ID：</strong>#{session.id}
        </Typography.Paragraph>
        <Typography.Paragraph style={{ margin: 0 }}>
          <strong>消息数：</strong>{session.messages.length}
        </Typography.Paragraph>
      </Card>

      <Card size="small" title="教学策略" style={{ marginBottom: 12 }}>
        {session.strategy ? (
          <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
            {session.strategy}
          </Typography.Paragraph>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={<span className="empty-tip">暂无策略数据</span>}
          />
        )}
      </Card>

      <Card size="small" title={`相关题目引用（${dedup.size}）`}>
        {dedup.size === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={<span className="empty-tip">无引用</span>}
          />
        ) : (
          Array.from(dedup.values()).map((ref) => (
            <div key={ref.id} style={{ marginBottom: 8 }}>
              <Tag>题目 #{ref.question_id}</Tag>
              {ref.similarity_score != null && (
                <Tag color="blue">相似度 {(ref.similarity_score * 100).toFixed(1)}%</Tag>
              )}
            </div>
          ))
        )}
        <Divider style={{ margin: '8px 0' }} />
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          引用来自教学过程中的相似题检索，实际内容需前往题库查看。
        </Typography.Text>
      </Card>
    </div>
  );
}
