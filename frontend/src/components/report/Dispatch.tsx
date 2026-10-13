import type { ReactNode } from 'react';
import dayjs from 'dayjs';
import PersonaAvatar from '@/components/theme/PersonaAvatar';
import { personaByKey, type PersonaKey } from '@/theme/personas';

interface Props {
  persona?: string | null;
  date: string;
  text: string;
  action?: ReactNode;
}

/** 讲师来信：横格信纸，页边线用讲师色，右上角邮戳 */
export default function Dispatch({ persona, date, text, action }: Props) {
  const key = (persona ?? 'leonard') as PersonaKey;
  const p = personaByKey(key);

  return (
    <section className="dispatch" style={{ ['--pc' as string]: p.color }} data-reveal>
      <div className="dispatch-stamp" aria-hidden="true">
        <span>Apt 4A</span>
        <b>{dayjs(date).format('MM.DD')}</b>
        <span>Pasadena</span>
      </div>
      <div className="dispatch-head">
        <PersonaAvatar persona={key} size={44} />
        <div>
          <span className="dispatch-label">Tonight's transmission</span>
          <span className="dispatch-from">来自 {p.name} 的周报</span>
        </div>
      </div>
      {/* key 随内容变：SplitText 拆过的节点整块换掉，不让 React 去改已被替换的文本 */}
      <p className="dispatch-text" key={text}>{text}</p>
      <div className="dispatch-foot">
        <span className="dispatch-sign">— {p.name}</span>
        {action}
      </div>
    </section>
  );
}
