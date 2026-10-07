import { personaAvatar, personaByKey, personaSilhouette, type PersonaKey } from '@/theme/personas';

interface Props {
  persona?: string | null;
  size?: number;
  locked?: boolean;
  className?: string;
  title?: string;
}

/** 讲师圆头像，主题色描边；locked 时显示剪影 */
export default function PersonaAvatar({ persona, size = 30, locked, className, title }: Props) {
  const p = personaByKey(persona);
  const src = locked ? personaSilhouette(p.key as PersonaKey) : personaAvatar(p.key as PersonaKey);
  return (
    <span
      className={`pavatar ${locked ? 'locked' : ''} ${className ?? ''}`}
      style={{ width: size, height: size, ['--pc' as string]: p.color }}
      title={title ?? p.name}
    >
      <img src={src} alt={p.name} draggable={false} />
    </span>
  );
}
