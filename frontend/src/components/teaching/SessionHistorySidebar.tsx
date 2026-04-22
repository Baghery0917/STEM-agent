import { Button, Empty, Spin, Tag, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { listTeachingSessions } from '@/api/teaching';
import type { TeachingSessionStatus } from '@/api/types';

interface Props {
  studentId: number;
  activeSessionId?: number;
}

const STATUS_TAG: Record<TeachingSessionStatus, { color: string; label: string }> = {
  active: { color: 'processing', label: '进行中' },
  completed: { color: 'success', label: '已完成' },
  cancelled: { color: 'default', label: '已取消' },
};

function formatTime(ts?: string | null): string {
  if (!ts) return '';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return '';
  const now = new Date();
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate();
  if (sameDay) {
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' });
}

export default function SessionHistorySidebar({ studentId, activeSessionId }: Props) {
  const navigate = useNavigate();

  const query = useQuery({
    queryKey: ['teaching-sessions', studentId],
    queryFn: () => listTeachingSessions(studentId, 50, 0),
    enabled: !!studentId,
  });

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#fff',
        borderRight: '1px solid #f0f0f0',
      }}
    >
      <div style={{ padding: 12, borderBottom: '1px solid #f0f0f0' }}>
        <Button
          type="primary"
          block
          icon={<PlusOutlined />}
          onClick={() => navigate('/teaching')}
        >
          新对话
        </Button>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
        {query.isLoading ? (
          <div style={{ textAlign: 'center', padding: 32 }}>
            <Spin size="small" />
          </div>
        ) : !query.data || query.data.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无历史会话"
            style={{ marginTop: 32 }}
          />
        ) : (
          query.data.map((s) => {
            const active = s.id === activeSessionId;
            const statusMeta = STATUS_TAG[s.status];
            return (
              <div
                key={s.id}
                onClick={() => navigate(`/teaching/${s.id}`)}
                style={{
                  padding: '10px 14px',
                  cursor: 'pointer',
                  background: active ? '#e6f4ff' : 'transparent',
                  borderLeft: active ? '3px solid #1677ff' : '3px solid transparent',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => {
                  if (!active) e.currentTarget.style.background = '#fafafa';
                }}
                onMouseLeave={(e) => {
                  if (!active) e.currentTarget.style.background = 'transparent';
                }}
              >
                <Typography.Paragraph
                  ellipsis={{ rows: 2 }}
                  style={{ margin: 0, fontSize: 13, lineHeight: 1.45 }}
                >
                  {s.preview || `会话 #${s.id}`}
                </Typography.Paragraph>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginTop: 4,
                    fontSize: 11,
                    color: '#8c8c8c',
                  }}
                >
                  <Tag color={statusMeta.color} style={{ margin: 0, fontSize: 11, lineHeight: '16px' }}>
                    {statusMeta.label}
                  </Tag>
                  <span>{formatTime(s.created_at)}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
