import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUiStore } from '@/stores/uiStore';
import { IconBack } from '@/components/theme/Icons';

interface Props {
  crumb: ReactNode;
  /** 是否显示 教学 | 练习 分段切换；报告、设置页隐藏 */
  showSeg?: boolean;
  /** true 时优先 history 回退，否则回教学；也可传绝对路径 */
  back?: boolean | string;
  right?: ReactNode;
}

export default function TopBar({ crumb, showSeg = true, back = false, right }: Props) {
  const mode = useUiStore((s) => s.mode);
  const navigate = useNavigate();

  const switchMode = (m: 'teaching' | 'practice') => {
    if (m === mode) return;
    navigate(m === 'practice' ? '/practice/new' : '/teaching');
  };

  const goBack = () => {
    if (typeof back === 'string') {
      navigate(back);
      return;
    }
    const idx = (window.history.state as { idx?: number } | null)?.idx;
    if (typeof idx === 'number' && idx > 0) navigate(-1);
    else navigate('/teaching');
  };

  return (
    <header className="topbar">
      <div className={`left ${back ? 'has-back' : ''}`}>
        {back ? (
          <button type="button" className="backbtn" onClick={goBack} aria-label="返回">
            <IconBack />
            <span>返回</span>
          </button>
        ) : null}
        <span className="crumb">{crumb}</span>
      </div>
      <div className={`seg ${showSeg ? '' : 'hidden'}`}>
        <div className="thumb" />
        <button type="button" className="b-t" onClick={() => switchMode('teaching')}><span className="d" />教学</button>
        <button type="button" className="b-p" onClick={() => switchMode('practice')}><span className="d" />练习</button>
      </div>
      <div className="right">
        {right}
      </div>
    </header>
  );
}
