/** 物理学家徽章：key 与后端 services/badges.py 的 BADGES 一致，阈值由后端下发 */
export type BadgeKey =
  | 'newton' | 'galileo' | 'tycho' | 'kepler' | 'curie' | 'faraday'
  | 'einstein' | 'hawking' | 'maxwell' | 'bohr' | 'heisenberg' | 'feynman';

export interface BadgeMeta {
  key: BadgeKey;
  /** 物理学家 */
  name: string;
  /** 徽章名，取自其标志性工作 */
  title: string;
  /** 条件描述，{n} 由后端阈值填充 */
  how: string;
  /** 获得时的一句话（该物理学家的名言或工作，中文） */
  quote: string;
  /** 徽章主色 */
  color: string;
  /** 符号：SVG 图标的 key，见 BadgeGlyph */
  glyph: 'apple' | 'telescope' | 'log' | 'orbit' | 'flask' | 'coil' | 'clock' | 'hourglass' | 'wave' | 'atom' | 'uncertain' | 'diagram';
}

export const BADGES: BadgeMeta[] = [
  { key: 'newton', name: 'Newton', title: '苹果落地', how: '答完第 {n} 题', quote: '我只是在海边捡贝壳的孩子。', color: '#c8322b', glyph: 'apple' },
  { key: 'galileo', name: 'Galileo', title: '望远镜', how: '登录 {n} 次', quote: '可它确实在动。', color: '#8A6D3B', glyph: 'telescope' },
  { key: 'tycho', name: 'Tycho', title: '观测日志', how: '登录 {n} 次', quote: '二十年，每一夜都记下来。', color: '#5B4A9E', glyph: 'log' },
  { key: 'kepler', name: 'Kepler', title: '行星周期', how: '连续学习 {n} 天', quote: '轨道是椭圆，不是圆。', color: '#1E8C4A', glyph: 'orbit' },
  { key: 'curie', name: 'Curie', title: '实验室长夜', how: '单次学习 {n} 分钟', quote: '生活中没有什么可怕的东西，只有需要理解的东西。', color: '#D9A520', glyph: 'flask' },
  { key: 'faraday', name: 'Faraday', title: '线圈不停', how: '单次学习 {n} 分钟', quote: '磁生电。', color: '#C8322B', glyph: 'coil' },
  { key: 'einstein', name: 'Einstein', title: '时间是相对的', how: '累计学习 {h} 小时', quote: '想象力比知识更重要。', color: '#1E8C4A', glyph: 'clock' },
  { key: 'hawking', name: 'Hawking', title: '时间简史', how: '累计学习 {h} 小时', quote: '抬头看星星，别低头看脚。', color: '#2a2118', glyph: 'hourglass' },
  { key: 'maxwell', name: 'Maxwell', title: '四个方程', how: '答完 {n} 题', quote: '要有光。', color: '#E0457B', glyph: 'wave' },
  { key: 'bohr', name: 'Bohr', title: '哥本哈根辩论', how: '完成 {n} 次教学会话', quote: '不要再告诉上帝该怎么做。', color: '#5F7A3D', glyph: 'atom' },
  { key: 'heisenberg', name: 'Heisenberg', title: '不确定就问', how: '星标后追问 {n} 次', quote: '测得越准，知道得越少。', color: '#a8731a', glyph: 'uncertain' },
  { key: 'feynman', name: 'Feynman', title: '讲给别人听', how: '自评「能讲给别人」{n} 次', quote: '讲不清楚，就是还没懂。', color: '#C8322B', glyph: 'diagram' },
];

export const badgeByKey = (key: string): BadgeMeta => BADGES.find((b) => b.key === key) ?? BADGES[0];

/** 把 how 里的占位符按阈值填好：分钟阈值 ≥ 60 用小时 */
export function badgeHow(meta: BadgeMeta, threshold: number): string {
  return meta.how.replace('{n}', String(threshold)).replace('{h}', String(Math.round(threshold / 60)));
}

export function badgeProgressText(metric: string, value: number, threshold: number): string {
  if (metric.endsWith('_minutes')) {
    const f = (m: number) => (m >= 90 ? `${(m / 60).toFixed(1).replace(/\.0$/, '')} 小时` : `${Math.round(m)} 分钟`);
    return `${f(value)} / ${f(threshold)}`;
  }
  if (metric === 'streak_days') return `${value} / ${threshold} 天`;
  return `${Math.min(value, threshold)} / ${threshold}`;
}
