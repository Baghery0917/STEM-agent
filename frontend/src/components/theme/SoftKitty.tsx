import { EMPTY } from '@/theme/copy';

interface Props {
  text?: string;
  variant?: 'phone' | 'cushion';
  compact?: boolean;
}

/** 空状态插画：Soft Kitty */
export default function SoftKitty({ text, variant = 'phone', compact }: Props) {
  const base = import.meta.env.BASE_URL;
  return (
    <div className={`kitty ${compact ? 'compact' : ''}`}>
      <img src={`${base}tbbt/illustrations/softkitty-${variant}.png`} alt="" />
      <div className="lyric">{EMPTY.kitty}</div>
      {text && <div className="note">{text}</div>}
    </div>
  );
}
