import { useCallback, useEffect, useRef, useState } from 'react';

const STORAGE_KEY = 'stem:camera-enabled';
const FRAME_WIDTH = 320;
const JPEG_QUALITY = 0.7;

export type CameraStatus = 'off' | 'starting' | 'on' | 'denied' | 'unavailable';

/**
 * 摄像头常驻预览，发送消息时抓一帧缩略 jpeg 给后端做面部情绪识别。
 * 画面只在本地 video 元素里，不录制、不上传视频流。
 */
export function useCameraFrame() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [enabled, setEnabledState] = useState<boolean>(() => {
    return localStorage.getItem(STORAGE_KEY) !== '0';
  });
  const [status, setStatus] = useState<CameraStatus>('off');

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setStatus('off');
  }, []);

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus('unavailable');
      return;
    }
    setStatus('starting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => undefined);
      }
      setStatus('on');
    } catch (err) {
      const name = (err as DOMException)?.name;
      setStatus(name === 'NotAllowedError' ? 'denied' : 'unavailable');
    }
  }, []);

  useEffect(() => {
    if (enabled) void start();
    else stop();
    return stop;
  }, [enabled, start, stop]);

  const setEnabled = useCallback((v: boolean) => {
    localStorage.setItem(STORAGE_KEY, v ? '1' : '0');
    setEnabledState(v);
  }, []);

  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || status !== 'on' || video.videoWidth === 0) return null;
    const scale = FRAME_WIDTH / video.videoWidth;
    const canvas = document.createElement('canvas');
    canvas.width = FRAME_WIDTH;
    canvas.height = Math.round(video.videoHeight * scale);
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', JPEG_QUALITY);
  }, [status]);

  return { videoRef, enabled, setEnabled, status, captureFrame };
}
