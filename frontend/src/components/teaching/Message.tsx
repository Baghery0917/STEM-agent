import type { ReactNode } from 'react';
import MarkdownContent from '@/components/common/MarkdownContent';

interface Props {
  role: 'user' | 'ai';
  who: string;
  content?: string;
  streaming?: boolean;
  before?: ReactNode;
  after?: ReactNode;
  /** user 消息：题目图片 */
  image?: string | null;
}

export default function Message({ role, who, content, streaming, before, after, image }: Props) {
  return (
    <div className={`msg ${role}`}>
      <div className="who">{who}</div>
      <div className="body">
        {before}
        {content != null && (role === 'ai'
          ? <MarkdownContent content={content} />
          : <div className="pre">{content}</div>)}
        {streaming && <span className="cursor" />}
        {image && (
          <div className="attach"><img src={image} alt="" />题目图片</div>
        )}
        {after}
      </div>
    </div>
  );
}
