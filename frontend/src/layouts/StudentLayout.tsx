import { useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Rail from '@/components/shell/Rail';
import Toasts from '@/components/shell/Toasts';
import { useRequireStudent } from '@/hooks/useRequireStudent';
import { useUiStore } from '@/stores/uiStore';

/** 学生端壳子：左侧会话栏 + 右侧主区。顶栏由各页面自己渲染（需要页面级上下文） */
export default function StudentLayout() {
  const student = useRequireStudent();
  const mode = useUiStore((s) => s.mode);
  const setMode = useUiStore((s) => s.setMode);
  const location = useLocation();
  const navigate = useNavigate();

  // 路由决定模式：/practice* 为练习，其余为教学；报告与设置不改模式
  useEffect(() => {
    if (location.pathname.startsWith('/practice')) setMode('practice');
    else if (location.pathname.startsWith('/teaching')) setMode('teaching');
  }, [location.pathname, setMode]);

  useEffect(() => {
    document.body.dataset.mode = mode;
  }, [mode]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        navigate(useUiStore.getState().mode === 'practice' ? '/practice/new' : '/teaching');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [navigate]);

  if (!student) return null;

  return (
    <div className="agent">
      <div className="app">
        <Rail />
        <main className="main">
          <Outlet />
        </main>
      </div>
      <Toasts />
    </div>
  );
}
