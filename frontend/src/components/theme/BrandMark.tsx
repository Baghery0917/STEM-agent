import { useId } from 'react';

interface Props { size?: number; className?: string }

/** 品牌标：渐变圆章 + 三轨原子 + 发光核心 */
export default function BrandMark({ size = 28, className }: Props) {
  const id = useId().replace(/:/g, '');
  return (
    <svg className={`brandmark-svg ${className ?? ''}`} width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-bg`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f2c94c" /><stop offset=".55" stopColor="#d9a520" /><stop offset="1" stopColor="#b8862a" />
        </linearGradient>
        <radialGradient id={`${id}-core`} cx=".5" cy=".5" r=".5">
          <stop offset="0" stopColor="#fff6dc" /><stop offset=".6" stopColor="#1e8c4a" /><stop offset="1" stopColor="#13602f" />
        </radialGradient>
        <radialGradient id={`${id}-glow`} cx=".5" cy=".5" r=".5">
          <stop offset="0" stopColor="#fff6dc" stopOpacity=".9" /><stop offset="1" stopColor="#fff6dc" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill={`url(#${id}-bg)`} />
      <circle cx="32" cy="32" r="30" fill="none" stroke="#2a2118" strokeOpacity=".18" strokeWidth="1.5" />
      <circle cx="32" cy="32" r="26.5" fill="none" stroke="#fff6dc" strokeOpacity=".45" strokeWidth="1" />
      <circle cx="32" cy="32" r="14" fill={`url(#${id}-glow)`} />
      <g fill="none" stroke="#2a2118" strokeWidth="2.2" strokeLinecap="round">
        <ellipse cx="32" cy="32" rx="20" ry="7.5" />
        <ellipse cx="32" cy="32" rx="20" ry="7.5" transform="rotate(60 32 32)" />
        <ellipse cx="32" cy="32" rx="20" ry="7.5" transform="rotate(120 32 32)" />
      </g>
      <g fill="#c8322b" stroke="#fff6dc" strokeWidth="1">
        <circle cx="52" cy="32" r="2.6" />
        <circle cx="22" cy="14.7" r="2.6" />
        <circle cx="22" cy="49.3" r="2.6" />
      </g>
      <circle cx="32" cy="32" r="5.2" fill={`url(#${id}-core)`} stroke="#fff6dc" strokeWidth="1.2" />
    </svg>
  );
}
