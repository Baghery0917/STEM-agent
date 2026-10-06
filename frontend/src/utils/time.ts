import dayjs from 'dayjs';

export function groupLabel(iso?: string | null): '今天' | '昨天' | '过去 7 天' | '更早' {
  if (!iso) return '更早';
  const d = dayjs(iso);
  const now = dayjs();
  if (d.isSame(now, 'day')) return '今天';
  if (d.isSame(now.subtract(1, 'day'), 'day')) return '昨天';
  if (d.isAfter(now.subtract(7, 'day'))) return '过去 7 天';
  return '更早';
}

export function shortTime(iso?: string | null): string {
  if (!iso) return '';
  const d = dayjs(iso);
  const now = dayjs();
  if (d.isSame(now, 'day')) return d.format('HH:mm');
  if (d.isSame(now, 'year')) return d.format('M月D日');
  return d.format('YYYY-M-D');
}

export function fmtDuration(sec?: number | null): string {
  if (sec == null) return '—';
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m}:${String(s).padStart(2, '0')}` : `${s}s`;
}

export function fmtClock(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
