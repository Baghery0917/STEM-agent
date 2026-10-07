import { useToastStore } from '@/stores/toastStore';

export default function Toasts() {
  const toasts = useToastStore((s) => s.toasts);
  if (!toasts.length) return null;
  return (
    <div className="toasts">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.kind === 'error' ? 'err' : ''}`}>{t.text}</div>
      ))}
    </div>
  );
}
