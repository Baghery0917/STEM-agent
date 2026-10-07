import { useEffect, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Rail from '@/components/shell/Rail';
import Toasts from '@/components/shell/Toasts';
import { useRequireStudent } from '@/hooks/useRequireStudent';
import { useUiStore } from '@/stores/uiStore';
import { useCards } from '@/hooks/useCards';
import CardReveal from '@/components/theme/CardReveal';
import type { PersonaKey } from '@/theme/personas';

/** 学生端壳子：左侧会话栏 + 右侧主区。顶栏由各页面自己渲染（需要页面级上下文） */
export default function StudentLayout() {
  const student = useRequireStudent();
  const mode = useUiStore((s) => s.mode);
  const setMode = useUiStore((s) => s.setMode);
  const location = useLocation();
  const navigate = useNavigate();
  const cards = useCards(student?.id);
  const [reveal, setReveal] = useState<PersonaKey | null>(null);

  // 新卡检测：和本地「已看过」集合比对，有未看过的就翻牌
  useEffect(() => {
    if (!student || !cards.data) return;
    const seenKey = `stem:cards-seen:${student.id}`;
    const seen = new Set<string>(JSON.parse(localStorage.getItem(seenKey) ?? '[]'));
    const fresh = cards.data.cards.map((c) => c.card_key).filter((k) => !seen.has(k));
    if (!fresh.length) return;
    if (seen.size === 0 && cards.data.cards.length > 1) {
      // 首次进入已有多张：全部视为看过，不连环弹窗
      localStorage.setItem(seenKey, JSON.stringify(cards.data.cards.map((c) => c.card_key)));
      return;
    }
    setReveal(fresh[0] as PersonaKey);
  }, [student, cards.data]);

  const closeReveal = () => {
    if (student && reveal) {
      const seenKey = `stem:cards-seen:${student.id}`;
      const seen = new Set<string>(JSON.parse(localStorage.getItem(seenKey) ?? '[]'));
      seen.add(reveal);
      localStorage.setItem(seenKey, JSON.stringify([...seen]));
    }
    setReveal(null);
  };

  // 路由决定模式：/practice* 为练习，其余为教学；报告与设置不改模式
  useEffect(() => {
    if (location.pathname.startsWith('/practice')) setMode('practice');
    else if (location.pathname.startsWith('/teaching')) setMode('teaching');
  }, [location.pathname, setMode]);

  useEffect(() => {
    document.body.dataset.mode = mode;
  }, [mode]);

  useEffect(() => {
    const page = location.pathname.split('/')[1] || 'teaching';
    document.body.dataset.page = page;
    return () => { delete document.body.dataset.page; };
  }, [location.pathname]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        navigate(location.pathname.startsWith('/practice') ? '/practice/new' : '/teaching');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [location.pathname, navigate]);

  if (!student) return null;

  return (
    <div className="agent">
      <div className="app">
        <Rail />
        <main className="main">
          <div className="page-transition" key={location.pathname}>
            <Outlet />
          </div>
        </main>
      </div>
      {reveal && <CardReveal cardKey={reveal} onClose={closeReveal} />}
      <Toasts />
    </div>
  );
}
