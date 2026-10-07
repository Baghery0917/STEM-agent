import type { ReactNode } from 'react';
import WeekdayIcon from './WeekdayIcon';
import { todayTheme } from '@/theme/weekday';

interface Props {
  eyebrow: string;
  title: ReactNode;
  description?: ReactNode;
  chapter?: string;
  actions?: ReactNode;
  art?: string;
  artAlt?: string;
  showToday?: boolean;
}

export default function ChapterHero({
  eyebrow,
  title,
  description,
  chapter,
  actions,
  art,
  artAlt = '',
  showToday = false,
}: Props) {
  const today = todayTheme();

  return (
    <header className={`chapter-hero ${art ? 'with-art' : ''}`}>
      <div className="chapter-copy">
        <div className="chapter-meta">
          {chapter && <span className="chapter-no">{chapter}</span>}
          <span className="chapter-eyebrow">{eyebrow}</span>
        </div>
        <h1>{title}</h1>
        {showToday && (
          <div className="chapter-today">
            <WeekdayIcon day={today.key} />
            <b>{today.en.split(' · ')[1]}</b>
            <span>{today.zh}</span>
          </div>
        )}
        {description && <div className="chapter-description">{description}</div>}
        {actions && <div className="chapter-actions">{actions}</div>}
      </div>
      {art && <img className="chapter-art" src={art} alt={artAlt} draggable={false} />}
    </header>
  );
}
