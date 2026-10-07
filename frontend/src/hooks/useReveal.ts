import { useEffect } from 'react';

/** 给 [data-reveal] 元素加 .in：进入视口时触发一次。root 是滚动容器。用 scroll 事件判定，不依赖 IntersectionObserver */
export function useReveal(root?: React.RefObject<HTMLElement>, deps: unknown[] = []) {
  useEffect(() => {
    const scope = root?.current ?? document.documentElement;
    const pending = new Set(Array.from(scope.querySelectorAll<HTMLElement>('[data-reveal]')));
    if (!pending.size) return;
    const check = () => {
      const vh = window.innerHeight;
      for (const el of pending) {
        if (el.getBoundingClientRect().top < vh * 0.94) { el.classList.add('in'); pending.delete(el); }
      }
    };
    check();
    scope.addEventListener('scroll', check, { passive: true });
    window.addEventListener('resize', check);
    return () => { scope.removeEventListener('scroll', check); window.removeEventListener('resize', check); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
