import type { ReactNode } from 'react';

interface Props {
  number?: string;
  eyebrow: string;
  title: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  tone?: 'paper' | 'dark' | 'plain';
  className?: string;
}

export default function SceneSection({
  number,
  eyebrow,
  title,
  aside,
  children,
  tone = 'paper',
  className = '',
}: Props) {
  return (
    <section className={`scene-section ${tone} ${className}`}>
      <div className="scene-heading">
        <div>
          <div className="scene-kicker">{number && <span>{number}</span>}{eyebrow}</div>
          <h2>{title}</h2>
        </div>
        {aside && <div className="scene-aside">{aside}</div>}
      </div>
      <div className="scene-content">{children}</div>
    </section>
  );
}
