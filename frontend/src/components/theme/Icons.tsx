import type { SVGProps } from 'react';

type P = SVGProps<SVGSVGElement>;
const base = (p: P): P => ({ width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true, ...p });

/** 原子：教学 */
export const IconAtom = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
    <ellipse cx="12" cy="12" rx="9" ry="3.6" />
    <ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(60 12 12)" />
    <ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(120 12 12)" />
  </svg>
);

/** 白板：练习 */
export const IconWhiteboard = (p: P) => (
  <svg {...base(p)}>
    <rect x="3" y="4" width="18" height="12" rx="1.5" />
    <path d="M7 9h6M7 12h4" />
    <path d="M9 16l-2 4M15 16l2 4" />
  </svg>
);

/** 沙发：学习报告（折线落在沙发上） */
export const IconCouch = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 13V9a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4" />
    <path d="M2 13h20v4H2z" />
    <path d="M4 17v2M20 17v2" />
    <path d="M7 11l3-2 2 1.5 3-2.5" />
  </svg>
);

/** 恒温器：设置（Sheldon 的 71°F） */
export const IconThermostat = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="8.5" />
    <circle cx="12" cy="12" r="4.5" />
    <path d="M12 7.5v2M12 12l2.2-1.3" />
  </svg>
);

/** 钥匙：认可卡 */
export const IconKey = (p: P) => (
  <svg {...base(p)}>
    <circle cx="8" cy="12" r="4" />
    <path d="M12 12h9M18 12v3M15 12v2" />
  </svg>
);

/** 坐垫：星标（Sheldon 的座位） */
export const IconCushion = (p: P) => (
  <svg {...base(p)}>
    <path d="M5 8c0-1 .8-2 2-2h10c1.2 0 2 1 2 2l1 9c0 1-.8 2-2 2H6c-1.2 0-2-1-2-2z" />
    <path d="M12 10v5" />
  </svg>
);

/** 门：切换学生 */
export const IconDoor = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 3h12v18H6z" />
    <circle cx="15" cy="12" r=".8" fill="currentColor" />
    <path d="M3 21h18" />
  </svg>
);
