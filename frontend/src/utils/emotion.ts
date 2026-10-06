/** 情绪数值 1=自信 … 5=非常受挫，与后端 app/external/emotion.py 对齐 */
export function emotionLabel(value: number | null | undefined): string | null {
  if (value == null) return null;
  const idx = Math.min(5, Math.max(1, Math.round(value)));
  return ['自信', '略犹豫', '气馁', '受挫', '非常受挫'][idx - 1];
}

export function emotionTone(value: number | null | undefined): 'good' | 'warn' | 'none' {
  if (value == null) return 'none';
  return value >= 3 ? 'warn' : 'good';
}

/** 把 1..5 映射成柱高百分比：状态越好柱子越高 */
export function emotionBarHeight(value: number | null | undefined): number {
  if (value == null) return 0;
  return Math.round(((6 - Math.min(5, Math.max(1, value))) / 5) * 100);
}
