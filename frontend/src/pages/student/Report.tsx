import { useQuery } from '@tanstack/react-query';
import { Card, Col, Empty, List, Progress, Row, Tabs, Tag, Typography } from 'antd';
import { getStudentReport } from '@/api/reports';
import { useStudentStore } from '@/stores/studentStore';
import NotImplementedCard from '@/components/common/NotImplementedCard';
import { formatRelative } from '@/utils/format';

export default function Report() {
  const student = useStudentStore((s) => s.current);

  const recentQuery = useQuery({
    queryKey: ['student-report', student?.id, 'recent'],
    queryFn: () => getStudentReport(student!.id, 'recent'),
    enabled: !!student,
  });

  const allQuery = useQuery({
    queryKey: ['student-report', student?.id, 'all'],
    queryFn: () => getStudentReport(student!.id, 'all'),
    enabled: !!student,
  });

  if (!student) return null;

  const renderRecent = () => {
    const data = recentQuery.data;
    return (
      <NotImplementedCard
        title="近一周动态（Recent 模式）"
        description="活跃知识点统计 + 近期情绪明细。待后端接口 GET /students/:id/report?mode=recent 上线后自动生效。"
      >
        <Row gutter={16}>
          <Col xs={24} md={14}>
            <Card size="small" title="活跃知识点" style={{ marginBottom: 16 }}>
              {data?.active_knowledge_points.length ? (
                <List
                  dataSource={data.active_knowledge_points}
                  renderItem={(kp) => (
                    <List.Item>
                      <List.Item.Meta
                        title={kp.section_title}
                        description={`练习 ${kp.total_practice_count} 次 · 教学 ${kp.total_teaching_count} 次`}
                      />
                      <Progress
                        percent={Math.round(kp.mastery_level * 100)}
                        style={{ width: 140 }}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Card>
          </Col>
          <Col xs={24} md={10}>
            <Card size="small" title="近期情绪明细">
              {data?.emotion_logs.length ? (
                <List
                  size="small"
                  dataSource={data.emotion_logs}
                  renderItem={(log) => (
                    <List.Item>
                      <Tag color={log.mode === 'teaching' ? 'purple' : 'cyan'}>
                        {log.mode}
                      </Tag>
                      <span style={{ marginRight: 8 }}>{log.section_title}</span>
                      <Tag>{log.emotion}</Tag>
                      <Typography.Text type="secondary" style={{ marginLeft: 'auto' }}>
                        {formatRelative(log.created_at)}
                      </Typography.Text>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无情绪数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Card>
          </Col>
        </Row>
      </NotImplementedCard>
    );
  };

  const renderAll = () => {
    const data = allQuery.data;
    return (
      <NotImplementedCard
        title="学习全景（All 模式）"
        description="全量知识点聚合 + 历史情绪趋势。待后端接口 GET /students/:id/report?mode=all 上线后自动生效。"
      >
        <Row gutter={16}>
          <Col xs={24} md={14}>
            <Card size="small" title="已学习知识点" style={{ marginBottom: 16 }}>
              {data?.active_knowledge_points.length ? (
                <List
                  dataSource={data.active_knowledge_points}
                  renderItem={(kp) => (
                    <List.Item>
                      <List.Item.Meta
                        title={kp.section_title}
                        description={`正确 ${kp.correct_count} / ${kp.total_practice_count}`}
                      />
                      <Progress
                        percent={Math.round(kp.mastery_level * 100)}
                        style={{ width: 140 }}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Card>
          </Col>
          <Col xs={24} md={10}>
            <Card size="small" title="情绪趋势（按知识点）">
              <Empty description="折线图待接入" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </Card>
          </Col>
        </Row>
      </NotImplementedCard>
    );
  };

  return (
    <div className="page-container">
      <Typography.Title level={3}>学习报告</Typography.Title>
      <Tabs
        defaultActiveKey="recent"
        items={[
          { key: 'recent', label: '近一周动态', children: renderRecent() },
          { key: 'all', label: '学习全景', children: renderAll() },
        ]}
      />
    </div>
  );
}
