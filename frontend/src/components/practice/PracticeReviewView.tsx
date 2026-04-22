import { Button, Card, Col, Empty, Result, Row, Space, Statistic, Tag, Typography } from 'antd';
import {
  CheckCircleFilled,
  CloseCircleFilled,
  ForwardOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { PracticeSessionDetailResponse } from '@/api/types';
import { DIFFICULTY_COLOR, DIFFICULTY_LABEL, QUESTION_TYPE_LABEL } from '@/utils/enums';

interface Props {
  session: PracticeSessionDetailResponse;
}

export default function PracticeReviewView({ session }: Props) {
  const navigate = useNavigate();
  const items = [...session.items].sort((a, b) => a.sequence - b.sequence);

  return (
    <div className="page-container" style={{ maxWidth: 960 }}>
      <Result
        status="info"
        title={`练习回顾 #${session.id}`}
        subTitle={`共作答 ${session.correct_count + session.wrong_count} 题，正确 ${session.correct_count} 题，跳过 ${session.skip_count} 题。`}
      />

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="正确" value={session.correct_count} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="错误" value={session.wrong_count} valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="跳过" value={session.skip_count} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="模式" value={session.mode} />
          </Card>
        </Col>
      </Row>

      {items.length === 0 ? (
        <Empty description="本次练习没有作答记录" />
      ) : (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {items.map((item, idx) => {
            const q = item.question;
            const correct = item.is_correct;
            const skipped = item.is_skipped;
            const borderColor = skipped
              ? '#d9d9d9'
              : correct
                ? '#52c41a'
                : '#ff4d4f';
            return (
              <Card
                key={item.id}
                size="small"
                style={{ borderColor }}
                title={
                  <Space>
                    <Typography.Text strong>第 {idx + 1} 题</Typography.Text>
                    {q && <Tag>{QUESTION_TYPE_LABEL[q.type]}</Tag>}
                    {q && (
                      <Tag color={DIFFICULTY_COLOR[q.difficulty]}>
                        {DIFFICULTY_LABEL[q.difficulty]}
                      </Tag>
                    )}
                    {skipped ? (
                      <Tag icon={<ForwardOutlined />} color="default">
                        已跳过
                      </Tag>
                    ) : correct ? (
                      <Tag icon={<CheckCircleFilled />} color="success">
                        正确
                      </Tag>
                    ) : (
                      <Tag icon={<CloseCircleFilled />} color="error">
                        错误
                      </Tag>
                    )}
                  </Space>
                }
              >
                {q ? (
                  <>
                    <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 12 }}>
                      {q.content}
                    </Typography.Paragraph>
                    {q.content_image && (
                      <img
                        src={q.content_image}
                        alt="题目图片"
                        style={{ maxWidth: '100%', borderRadius: 6, marginBottom: 12 }}
                      />
                    )}
                    {!skipped && (
                      <div style={{ marginBottom: 8 }}>
                        <Typography.Text type="secondary">我的答案：</Typography.Text>
                        <Typography.Text>{item.user_answer || '(空)'}</Typography.Text>
                      </div>
                    )}
                    <div style={{ marginBottom: 8 }}>
                      <Typography.Text type="secondary">正确答案：</Typography.Text>
                      <Typography.Text strong>{q.answer}</Typography.Text>
                    </div>
                    {q.analysis && (
                      <div
                        style={{
                          background: '#fafafa',
                          padding: 12,
                          borderRadius: 4,
                          marginTop: 8,
                        }}
                      >
                        <Typography.Text type="secondary">解析：</Typography.Text>
                        <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                          {q.analysis}
                        </Typography.Paragraph>
                      </div>
                    )}
                  </>
                ) : (
                  <Typography.Text type="secondary">题目信息缺失 (question_id={item.question_id})</Typography.Text>
                )}
              </Card>
            );
          })}
        </Space>
      )}

      <Space style={{ marginTop: 24 }}>
        <Button type="primary" onClick={() => navigate('/practice/setup')}>
          再来一组
        </Button>
        <Button onClick={() => navigate('/practice/history')}>返回历史</Button>
      </Space>
    </div>
  );
}
