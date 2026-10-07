import type { SVGProps } from 'react';
import type { WeekdayKey } from '@/theme/weekday';

type P = SVGProps<SVGSVGElement> & { day: WeekdayKey };
const base = (p: Omit<P, 'day'>) => ({ width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true, ...p });

/** 每天一个小图标：外卖盒、蛋糕、漫画、披萨、手柄、洗衣机、沙发 */
export default function WeekdayIcon({ day, ...p }: P) {
  const b = base(p);
  switch (day) {
    case 'thai': return <svg {...b}><path d="M5 9h14l-1.5 11h-11z" /><path d="M8 9V6a4 4 0 0 1 8 0v3" /><path d="M9 13h6" /></svg>;
    case 'cheesecake': return <svg {...b}><path d="M3 20h18" /><path d="M4 20l2-9h12l2 9" /><path d="M6 11c3-6 9-6 12 0" /><circle cx="12" cy="7" r="1.2" fill="currentColor" stroke="none" /></svg>;
    case 'comic': return <svg {...b}><path d="M4 5h7a2 2 0 0 1 2 2v13H6a2 2 0 0 1-2-2z" /><path d="M20 5h-7v15h5a2 2 0 0 0 2-2z" /><path d="M7 9h3M7 12h3" /></svg>;
    case 'pizza': return <svg {...b}><path d="M12 21L3 6c6-3 12-3 18 0z" /><circle cx="10" cy="10" r="1.3" fill="currentColor" stroke="none" /><circle cx="14" cy="12" r="1.3" fill="currentColor" stroke="none" /><circle cx="11.5" cy="15" r="1.3" fill="currentColor" stroke="none" /></svg>;
    case 'game': return <svg {...b}><rect x="3" y="8" width="18" height="10" rx="4" /><path d="M8 11v4M6 13h4" /><circle cx="16" cy="12" r=".9" fill="currentColor" stroke="none" /><circle cx="18" cy="14" r=".9" fill="currentColor" stroke="none" /></svg>;
    case 'laundry': return <svg {...b}><rect x="4" y="3" width="16" height="18" rx="2" /><circle cx="12" cy="13" r="4.5" /><path d="M7 6h2M11 6h2" /><path d="M9.5 13.5c1.5-1.2 3.5-1.2 5 0" /></svg>;
    default: return <svg {...b}><path d="M4 13V9a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4" /><path d="M2 13h20v4H2z" /><path d="M4 17v2M20 17v2" /></svg>;
  }
}
