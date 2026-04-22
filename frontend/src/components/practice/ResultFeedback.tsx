import { Alert, Card, Divider, Typography } from 'antd';
import type { PracticeItemResponse, QuestionResponse } from '@/api/types';

interface Props {
  item: PracticeItemResponse;
  question: QuestionResponse;
}

export default function ResultFeedback({ item, question }: Props) {
  return (
    <Card
      size="small"
      style={{
        borderColor: item.is_correct ? '#52c41a' : '#ff4d4f',
        background: item.is_correct ? '#f6ffed' : '#fff1f0',
      }}
    >
      <Alert
        type={item.is_correct ? 'success' : 'error'}
        showIcon
        message={item.is_correct ? '回答正确！' : '回答错误'}
        description={
          <div>
            <div>
              <strong>你的答案：</strong>
              {item.user_answer}
            </div>
            <div>
              <strong>参考答案：</strong>
              {question.answer}
            </div>
          </div>
        }
      />
      {question.analysis && (
        <>
          <Divider style={{ margin: '12px 0' }} />
          <Typography.Title level={5}>答案解析</Typography.Title>
          <Typography.Paragraph style={{ whiteSpace: 'pre-wrap' }}>
            {question.analysis}
          </Typography.Paragraph>
        </>
      )}
      {question.analysis_image && (
        <img
          src={question.analysis_image}
          alt="解析图片"
          style={{ maxWidth: '100%', borderRadius: 6 }}
        />
      )}
    </Card>
  );
}
