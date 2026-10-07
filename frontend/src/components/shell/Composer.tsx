import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

interface Props {
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  modeHint?: string;
  /** 上方的上下文标签，如来源题、图片 */
  context?: ReactNode;
  onSend: (text: string, image?: string | null) => void;
  allowImage?: boolean;
  autoFocus?: boolean;
  /** 工具栏最左侧：当前讲师头像 */
  leading?: ReactNode;
}

/** 底部悬浮输入框。Enter 发送，Shift+Enter 换行，支持粘贴图片 URL / 文件 */
export default function Composer({
  placeholder, disabled, loading, modeHint, context, onSend, allowImage = true, autoFocus, leading,
}: Props) {
  const [text, setText] = useState('');
  const [image, setImage] = useState<string | null>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(200, ta.scrollHeight)}px`;
  }, [text]);

  useEffect(() => {
    if (autoFocus) taRef.current?.focus();
  }, [autoFocus]);

  const canSend = !disabled && !loading && (text.trim().length > 0 || !!image);

  const send = () => {
    if (!canSend) return;
    onSend(text.trim(), image);
    setText('');
    setImage(null);
  };

  const pickFile = (file: File) => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = () => setImage(String(reader.result));
    reader.readAsDataURL(file);
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        {(context || image) && (
          <div className="ctx">
            {context}
            {image && (
              <span className="tg">
                图片已附上 <span className="x" onClick={() => setImage(null)}>×</span>
              </span>
            )}
          </div>
        )}
        <div className="box">
          <textarea
            ref={taRef}
            rows={1}
            value={text}
            disabled={disabled}
            placeholder={placeholder ?? '输入题目，或粘贴 / 拖入题目截图…'}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                send();
              }
            }}
            onPaste={(e) => {
              const f = Array.from(e.clipboardData.files)[0];
              if (f && allowImage) pickFile(f);
            }}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files[0];
              if (f && allowImage) pickFile(f);
            }}
            onDragOver={(e) => e.preventDefault()}
          />
          <div className="tools">
            {leading}
            {allowImage && (
              <>
                <button type="button" className="iconbtn" title="上传图片 / 拍照" onClick={() => fileRef.current?.click()} disabled={disabled}>⊕</button>
                <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => e.target.files?.[0] && pickFile(e.target.files[0])} />
              </>
            )}
            {modeHint && <span className="modehint">{modeHint}</span>}
            <button type="button" className="send" title="发送（↵）" disabled={!canSend} onClick={send}>
              {loading ? <span className="spin-sm" /> : '↑'}
            </button>
          </div>
        </div>
        <div className="foot">讲解由 AI 生成，关键结论请对照课本核实。</div>
      </div>
    </div>
  );
}
