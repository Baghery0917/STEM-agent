import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUiStore } from '@/stores/uiStore';

interface Props {
  crumb: ReactNode;
  /** 是否显示 教学 | 练习 分段切换；报告、设置页隐藏 */
  showSeg?: boolean;
  right?: ReactNode;
}

export default function TopBar({ crumb, showSeg = true, right }: Props) {
  const mode = useUiStore((s) => s.mode);
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);
  const navigate = useNavigate();

  const switchMode = (m: 'teaching' | 'practice') => {
    if (m === mode) return;
    navigate(m === 'practice' ? '/practice/new' : '/teaching');
  };

  return (
    <header className="topbar">
      <div className="left"><span className="crumb">{crumb}</span></div>
      <div className={`seg ${showSeg ? '' : 'hidden'}`}>
        <div className="thumb" />
        <button type="button" className="b-t" onClick={() => switchMode('teaching')}><span className="d" />教学</button>
        <button type="button" className="b-p" onClick={() => switchMode('practice')}><span className="d" />练习</button>
      </div>
      <div className="right">
        {right}
        <button
          type="button"
          className="iconbtn"
          title="切换主题"
          onClick={() => setTheme(document.body.dataset.theme === 'dark' ? 'light' : 'dark')}
          aria-label={`当前主题 ${theme}`}
        >◐</button>
      </div>
    </header>
  );
}
