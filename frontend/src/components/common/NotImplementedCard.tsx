import { Alert, Card } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import type { ReactNode } from 'react';

interface Props {
  title: string;
  description?: string;
  children?: ReactNode;
}

export default function NotImplementedCard({ title, description, children }: Props) {
  return (
    <Card
      style={{
        border: '1px dashed #d9d9d9',
        background: 'rgba(255, 247, 230, 0.4)',
      }}
      title={
        <span>
          <InfoCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
          {title}
        </span>
      }
    >
      <Alert
        showIcon
        type="info"
        message="后端接口待补充"
        description={description ?? '此功能依赖的后端接口尚未实现，以下为界面占位。'}
        style={{ marginBottom: 16 }}
      />
      {children}
    </Card>
  );
}
