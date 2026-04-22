import { Avatar, Card, Tag, Typography } from 'antd';
import { RobotOutlined, UserOutlined } from '@ant-design/icons';
import type { TeachingMessageResponse } from '@/api/types';
import { MESSAGE_TYPE_LABEL } from '@/utils/enums';
import MarkdownContent from '@/components/common/MarkdownContent';

interface Props {
  message: TeachingMessageResponse;
  streaming?: boolean;
}

export default function ChatBubble({ message, streaming }: Props) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem && message.message_type !== 'chat') {
    return (
      <Card
        size="small"
        style={{ marginBottom: 12, background: '#fafafa', border: '1px dashed #d9d9d9' }}
      >
        <Tag color="default">{MESSAGE_TYPE_LABEL[message.message_type] ?? '系统'}</Tag>
        <Typography.Paragraph
          type="secondary"
          style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap', fontSize: 12 }}
          ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
        >
          {message.content}
        </Typography.Paragraph>
      </Card>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: 12,
        marginBottom: 16,
      }}
    >
      <Avatar
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{ background: isUser ? '#2563eb' : '#10b981', flexShrink: 0 }}
      />
      <div
        style={{
          maxWidth: '78%',
          padding: '10px 14px',
          borderRadius: 10,
          background: isUser ? '#2563eb' : '#fff',
          color: isUser ? '#fff' : '#1f2937',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
          lineHeight: 1.6,
        }}
      >
        <MarkdownContent content={message.content || (streaming ? '' : '')} />
        {streaming && <span className="stream-cursor" />}
      </div>
    </div>
  );
}
