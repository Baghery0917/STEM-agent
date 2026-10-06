import { Switch, Tooltip, Typography } from 'antd';
import { CameraOutlined } from '@ant-design/icons';
import type { RefObject } from 'react';
import type { CameraStatus } from '@/hooks/useCameraFrame';

interface Props {
  videoRef: RefObject<HTMLVideoElement>;
  enabled: boolean;
  status: CameraStatus;
  onToggle: (v: boolean) => void;
}

const STATUS_TEXT: Record<CameraStatus, string> = {
  off: '已关闭',
  starting: '启动中…',
  on: '识别中',
  denied: '未授权',
  unavailable: '不可用',
};

export default function CameraWidget({ videoRef, enabled, status, onToggle }: Props) {
  return (
    <div
      style={{
        position: 'absolute',
        left: 16,
        bottom: 112,
        width: 160,
        borderRadius: 12,
        overflow: 'hidden',
        background: '#111',
        boxShadow: '0 4px 16px rgba(0,0,0,.18)',
        zIndex: 5,
      }}
    >
      <video
        ref={videoRef}
        muted
        playsInline
        style={{
          display: enabled && status === 'on' ? 'block' : 'none',
          width: '100%',
          height: 120,
          objectFit: 'cover',
          transform: 'scaleX(-1)',
        }}
      />
      {!(enabled && status === 'on') && (
        <div
          style={{
            height: 120,
            display: 'grid',
            placeItems: 'center',
            color: '#777',
            fontSize: 12,
          }}
        >
          <CameraOutlined style={{ fontSize: 22 }} />
        </div>
      )}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 10px',
          background: '#1c1c1c',
        }}
      >
        <Tooltip title="发送消息时抓一帧判断学习状态，只用于调整讲解方式。画面不上传不保存。">
          <Typography.Text style={{ color: '#ccc', fontSize: 12, flex: 1 }}>
            状态 · {STATUS_TEXT[enabled ? status : 'off']}
          </Typography.Text>
        </Tooltip>
        <Switch size="small" checked={enabled} onChange={onToggle} />
      </div>
    </div>
  );
}
