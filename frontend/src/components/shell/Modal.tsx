import type { ReactNode } from 'react';

interface Props {
  open: boolean;
  title: string;
  children?: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
}

export default function Modal({ open, title, children, onClose, footer }: Props) {
  if (!open) return null;
  return (
    <div className="mask" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true">
        <h3>{title}</h3>
        {children}
        {footer && <div className="mf">{footer}</div>}
      </div>
    </div>
  );
}
