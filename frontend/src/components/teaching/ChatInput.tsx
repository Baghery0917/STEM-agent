import { Button, Input, Space } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useState } from 'react';

interface Props {
  loading?: boolean;
  disabled?: boolean;
  onSend: (value: string) => void;
  placeholder?: string;
}

export default function ChatInput({ loading, disabled, onSend, placeholder }: Props) {
  const [value, setValue] = useState('');

  const send = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <div style={{ padding: 16, borderTop: '1px solid #f0f0f0', background: '#fff' }}>
      <Space.Compact style={{ width: '100%' }}>
        <Input.TextArea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder ?? '继续追问...'}
          autoSize={{ minRows: 2, maxRows: 6 }}
          disabled={disabled}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          loading={loading}
          disabled={disabled || !value.trim()}
          onClick={send}
          style={{ height: 'auto' }}
        >
          发送
        </Button>
      </Space.Compact>
      <div style={{ fontSize: 12, color: '#bfbfbf', marginTop: 4 }}>
        Enter 发送 · Shift+Enter 换行
      </div>
    </div>
  );
}
