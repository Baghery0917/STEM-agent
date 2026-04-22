import { useEffect, useState } from 'react';
import { Statistic } from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';

interface Props {
  startedAt: number;
  running: boolean;
}

export default function ThinkingTimer({ startedAt, running }: Props) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [running]);

  const elapsedSec = Math.max(0, Math.floor((now - startedAt) / 1000));
  const m = Math.floor(elapsedSec / 60);
  const s = elapsedSec % 60;

  return (
    <Statistic
      title="思考时长"
      value={`${m}:${s.toString().padStart(2, '0')}`}
      prefix={<ClockCircleOutlined />}
      valueStyle={{ fontSize: 18 }}
    />
  );
}
