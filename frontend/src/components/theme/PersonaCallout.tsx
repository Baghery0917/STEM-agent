import type { ReactNode } from 'react';
import PersonaAvatar from './PersonaAvatar';
import { personaByKey, type PersonaKey } from '@/theme/personas';

interface Props {
  persona?: string | null;
  label?: string;
  children: ReactNode;
  action?: ReactNode;
  dark?: boolean;
}

export default function PersonaCallout({ persona, label, children, action, dark = false }: Props) {
  const key = (persona ?? 'leonard') as PersonaKey;
  const detail = personaByKey(key);

  return (
    <div className={`persona-callout ${dark ? 'dark' : ''}`} style={{ ['--pc' as string]: detail.color }}>
      <PersonaAvatar persona={key} size={38} />
      <div className="persona-callout-copy">
        <span>{label ?? `${detail.name} 的便签`}</span>
        <div>{children}</div>
      </div>
      {action && <div className="persona-callout-action">{action}</div>}
    </div>
  );
}
