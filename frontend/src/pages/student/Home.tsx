import { Card, Col, Row, Statistic, Typography } from 'antd';
import {
  CommentOutlined,
  ExperimentOutlined,
  LineChartOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useStudentStore } from '@/stores/studentStore';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import { useQuery } from '@tanstack/react-query';
import { listQuestions } from '@/api/questions';
import { GENDER_LABEL } from '@/utils/enums';

export default function Home() {
  const student = useStudentStore((s) => s.current);
  const navigate = useNavigate();
  const tree = useKnowledgeTree();
  const questionsQuery = useQuery({
    queryKey: ['questions', 'count'],
    queryFn: () => listQuestions({ limit: 1 }),
  });

  if (!student) return null;

  const cards = [
    {
      key: 'teaching',
      title: '教学对话',
      description: '提交题目，让 AI 按照你的画像个性化讲解。',
      icon: <CommentOutlined />,
      color: '#2563eb',
      to: '/teaching',
    },
    {
      key: 'practice',
      title: '开始练习',
      description: '按知识点与难度进行 Focused / General 练习。',
      icon: <ExperimentOutlined />,
      color: '#10b981',
      to: '/practice/setup',
    },
    {
      key: 'report',
      title: '学习报告',
      description: '查看近期活跃与学习全景。',
      icon: <LineChartOutlined />,
      color: '#f59e0b',
      to: '/report',
    },
  ];

  return (
    <div className="page-container">
      <Typography.Title level={2} style={{ marginBottom: 4 }}>
        你好，{student.name} 👋
      </Typography.Title>
      <Typography.Text type="secondary">
        {GENDER_LABEL[student.gender]} · Student ID #{student.id}
      </Typography.Text>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="知识篇（Volume）" value={tree.data?.volumes.length ?? 0} loading={tree.isLoading} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="章（Chapter）" value={tree.data?.chapters.length ?? 0} loading={tree.isLoading} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="节 / 知识点" value={tree.data?.sections.length ?? 0} loading={tree.isLoading} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="题库（本页）"
              value={questionsQuery.data?.length ?? 0}
              loading={questionsQuery.isLoading}
              suffix="+"
            />
          </Card>
        </Col>
      </Row>

      <Typography.Title level={4} style={{ marginTop: 32, marginBottom: 16 }}>
        快速入口
      </Typography.Title>
      <Row gutter={[16, 16]}>
        {cards.map((card) => (
          <Col xs={24} md={8} key={card.key}>
            <Card
              hoverable
              onClick={() => navigate(card.to)}
              style={{ borderTop: `3px solid ${card.color}` }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 12,
                    background: `${card.color}22`,
                    color: card.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 28,
                  }}
                >
                  {card.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <Typography.Title level={5} style={{ margin: 0 }}>
                    {card.title}
                  </Typography.Title>
                  <Typography.Text type="secondary">{card.description}</Typography.Text>
                </div>
                <RightOutlined style={{ color: '#bfbfbf' }} />
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
