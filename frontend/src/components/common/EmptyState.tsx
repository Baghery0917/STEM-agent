import { Empty } from 'antd';
import type { ReactNode } from 'react';

export default function EmptyState({
  description,
  children,
}: {
  description?: string;
  children?: ReactNode;
}) {
  return (
    <Empty description={description ?? '暂无数据'} style={{ padding: '40px 0' }}>
      {children}
    </Empty>
  );
}
