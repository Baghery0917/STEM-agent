import type { SVGProps } from 'react';
import type { BadgeMeta } from '@/theme/badges';

type P = SVGProps<SVGSVGElement>;
const base = (p: P): P => ({ width: 22, height: 22, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true, ...p });

/** 徽章图标：一人一个线条符号 */
export default function BadgeGlyph({ glyph, ...p }: { glyph: BadgeMeta['glyph'] } & P) {
  switch (glyph) {
    case 'apple': return <svg {...base(p)}><path d="M12 7c-3.5-2-7 .5-7 5s3 8 5 8c1 0 1.5-.5 2-.5s1 .5 2 .5c2 0 5-3.5 5-8s-3.5-7-7-5z" /><path d="M12 7c0-2 1-3.5 3-4" /></svg>;
    case 'telescope': return <svg {...base(p)}><path d="M3 14l13-7 2 4-13 7z" /><path d="M16 7l3-1.5 2 4L18 11" /><path d="M10 15l-2 6M12 14l2 7" /></svg>;
    case 'log': return <svg {...base(p)}><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M9 8h6M9 12h6M9 16h4" /></svg>;
    case 'orbit': return <svg {...base(p)}><ellipse cx="12" cy="12" rx="9" ry="5" /><circle cx="12" cy="12" r="2" fill="currentColor" stroke="none" /><circle cx="20" cy="10" r="1.6" fill="currentColor" stroke="none" /></svg>;
    case 'flask': return <svg {...base(p)}><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3" /><path d="M8 15h8" /></svg>;
    case 'coil': return <svg {...base(p)}><path d="M3 12h2c0-3 4-3 4 0s4 3 4 0 4-3 4 0 4 3 4 0h-1" /><path d="M3 7h18M3 17h18" opacity=".5" /></svg>;
    case 'clock': return <svg {...base(p)}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>;
    case 'hourglass': return <svg {...base(p)}><path d="M6 3h12M6 21h12M8 3c0 5 4 6 4 9s-4 4-4 9M16 3c0 5-4 6-4 9s4 4 4 9" /></svg>;
    case 'wave': return <svg {...base(p)}><path d="M3 12c2-5 4-5 6 0s4 5 6 0 4-5 6 0" /><path d="M3 12h18" opacity=".4" /></svg>;
    case 'atom': return <svg {...base(p)}><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" /><ellipse cx="12" cy="12" rx="9" ry="3.5" /><ellipse cx="12" cy="12" rx="9" ry="3.5" transform="rotate(60 12 12)" /><ellipse cx="12" cy="12" rx="9" ry="3.5" transform="rotate(120 12 12)" /></svg>;
    case 'uncertain': return <svg {...base(p)}><path d="M5 18c3-9 11-9 14 0" /><path d="M9 18c1-4 5-4 6 0" opacity=".5" /><path d="M12 4v2" /></svg>;
    case 'diagram': return <svg {...base(p)}><path d="M4 18l8-6 8 6M12 12V5" /><path d="M9 5c1 1 1 2 0 3s-1 2 0 3M15 5c-1 1-1 2 0 3s1 2 0 3" opacity=".6" /></svg>;
  }
}
