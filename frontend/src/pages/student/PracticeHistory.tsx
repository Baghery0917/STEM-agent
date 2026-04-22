import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Empty, Space, Spin, Table, Tag, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { listPracticeSessions } from '@/api/practice';
import { useStudentStore } from '@/stores/studentStore';
import type { PracticeSessionResponse } from '@/api/types';
import { PRACTICE_MODE_LABEL } from '@/utils/enums';

const PAGE_SIZE = 20;

function formatDateTime(ts?: string | null): string {
  if (!ts) return '-';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return '-';
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function PracticeHistory() {
  const student = useStudentStore((s) => s.current);
  const navigate = useNavigate();
  const [rows, setRows] = useState<PracticeSessionResponse[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const query = useQuery({
    queryKey: ['practice-sessions', student?.id, offset],
    queryFn: async () => {
      const data = await listPracticeSessions(student!.id, PAGE_SIZE, offset);
      setRows((prev) => (offset === 0 ? data : [...prev, ...data]));
      setHasMore(data.length === PAGE_SIZE);
      return data;
    },
    enabled: !!student,
  });

  if (!student) return null;

  const columns = [
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (v: string) => formatDateTime(v),
    },
    {
      title: '模式',
      dataIndex: 'mode',
      key: 'mode',
      render: (v: 'focused' | 'general') => (
        <Tag color={v === 'focused' ? 'blue' : 'geekblue'}>
          {PRACTICE_MODE_LABEL[v]}
        </Tag>
      ),
    },
    {
      title: '知识点数',
      key: 'kp_count',
      render: (_: unknown, r: PracticeSessionResponse) => r.knowledge_point_ids.length,
    },
    {
      title: '总题数',
      dataIndex: 'total_count',
      key: 'total_count',
    },
    {
      title: '正确',
      dataIndex: 'correct_count',
      key: 'correct_count',
      render: (v: number) => <span style={{ color: '#52c41a' }}>{v}</span>,
    },
    {
      title: '错误',
      dataIndex: 'wrong_count',
      key: 'wrong_count',
      render: (v: number) => <span style={{ color: '#ff4d4f' }}>{v}</span>,
    },
    {
      title: '跳过',
      dataIndex: 'skip_count',
      key: 'skip_count',
    },
    {
      title: '状态',
      key: 'status',
      render: (_: unknown, r: PracticeSessionResponse) =>
        r.ended_at ? (
          <Tag color="success">已完成</Tag>
        ) : (
          <Tag color="processing">进行中</Tag>
        ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, r: PracticeSessionResponse) => (
        <Button type="link" onClick={() => navigate(`/practice/${r.id}`)}>
          {r.ended_at ? '查看回顾' : '继续练习'}
        </Button>
      ),
    },
  ];

  return (
    <div className="page-container" style={{ maxWidth: 1100 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16,
        }}
      >
        <Typography.Title level={3} style={{ margin: 0 }}>
          练习历史
        </Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/practice/setup')}
        >
          开始新练习
        </Button>
      </div>

      <Card>
        {query.isLoading && rows.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <Spin />
          </div>
        ) : rows.length === 0 ? (
          <Empty description="还没有练习记录" />
        ) : (
          <>
            <Table
              rowKey="id"
              columns={columns}
              dataSource={rows}
              pagination={false}
              onRow={(r) => ({
                onClick: () => navigate(`/practice/${r.id}`),
                style: { cursor: 'pointer' },
              })}
            />
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Space>
                {hasMore ? (
                  <Button
                    onClick={() => setOffset(offset + PAGE_SIZE)}
                    loading={query.isFetching}
                  >
                    加载更多
                  </Button>
                ) : (
                  <Typography.Text type="secondary">已到底部</Typography.Text>
                )}
              </Space>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
