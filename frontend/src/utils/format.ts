import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

export function formatDateTime(value?: string | null) {
  if (!value) return '—';
  return dayjs(value).format('YYYY-MM-DD HH:mm');
}

export function formatRelative(value?: string | null) {
  if (!value) return '—';
  return dayjs(value).fromNow();
}

export function formatDuration(startedAt?: string | null, endedAt?: string | null) {
  if (!startedAt) return '—';
  const end = endedAt ? dayjs(endedAt) : dayjs();
  const ms = end.diff(dayjs(startedAt));
  const totalSec = Math.max(0, Math.round(ms / 1000));
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}分${s.toString().padStart(2, '0')}秒`;
}
