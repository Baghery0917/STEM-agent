import { useEffect, useRef, useState } from 'react';
import type { RefObject } from 'react';
import type { CameraStatus } from '@/hooks/useCameraFrame';
import { emotionLabel, emotionTone } from '@/utils/emotion';

interface Props {
  videoRef: RefObject<HTMLVideoElement>;
  enabled: boolean;
  status: CameraStatus;
  onToggle: (v: boolean) => void;
  /** 最近一次后端返回的即时情绪值（1-5），用于顶栏文案 */
  latestValue?: number | null;
}

const STATUS_TEXT: Record<CameraStatus, string> = {
  off: '已关闭',
  starting: '启动中…',
  on: '识别中',
  denied: '未授权',
  unavailable: '不可用',
};

/** 顶栏右侧的情绪状态胶囊：点开可看摄像头预览与开关 */
export default function EmotionBadge({ videoRef, enabled, status, onToggle, latestValue }: Props) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const live = enabled && status === 'on';
  const label = latestValue != null ? `状态：${emotionLabel(latestValue)}` : live ? '状态：识别中' : '情绪识别已关';
  const dotCls = !live ? '' : emotionTone(latestValue) === 'warn' ? 'on warn' : 'on';

  return (
    <div className="emo" ref={wrapRef} style={{ cursor: 'pointer' }} onClick={() => setOpen((v) => !v)}>
      <span className={`cam ${dotCls}`} />
      {label}
      {open && (
        <div className="emo-pop" onClick={(e) => e.stopPropagation()}>
          <video ref={videoRef} muted playsInline style={{ display: live ? 'block' : 'none' }} />
          {!live && (
            <div style={{ height: 150, display: 'grid', placeItems: 'center', background: 'var(--line-2)', borderRadius: 8 }}>
              {STATUS_TEXT[enabled ? status : 'off']}
            </div>
          )}
          <div className="row">
            <span>发送消息时抓一帧判断学习状态，只用于调整讲解节奏。画面不上传不保存。</span>
            <button
              type="button"
              className={`toggle ${enabled ? 'on' : ''}`}
              aria-label="切换情绪识别"
              onClick={() => onToggle(!enabled)}
            />
          </div>
        </div>
      )}
      {/* 关闭弹层时 video 仍需挂载以保持流 */}
      {!open && <video ref={videoRef} muted playsInline style={{ display: 'none' }} />}
    </div>
  );
}
