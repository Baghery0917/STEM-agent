import type { ReactNode } from 'react';
import MarkdownContent from '@/components/common/MarkdownContent';
import PersonaAvatar from '@/components/theme/PersonaAvatar';
import { personaByKey } from '@/theme/personas';

interface Props {
  role: 'user' | 'ai';
  who: string;
  content?: string;
  streaming?: boolean;
  before?: ReactNode;
  after?: ReactNode;
  /** user 消息：题目图片 */
  image?: string | null;
  /** ai 消息：讲师 */
  persona?: string | null;
}

export default function Message({ role, who, content, streaming, before, after, image, persona }: Props) {
  const p = role === 'ai' ? personaByKey(persona) : null;
  return (
    <div className={`msg ${role}`} style={p ? { ['--pc' as string]: p.color } : undefined}>
      {role === 'ai' ? <PersonaAvatar persona={persona} size={30} className="who" /> : <div className="who">{who}</div>}
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
