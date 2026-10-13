import { useEffect, type RefObject } from 'react';

/**
 * 滚动驱动引擎。每帧（rAF 节流）测量 scope 内带标记的元素，把进度写进 CSS 变量，
 * 由样式层把进度映射成位移、缩放、透明度。滚动时不触发 React 重渲染。
 *
 * 标记：
 *   data-scroll="pin"    高容器 + 内部 sticky。--p：容器顶到达滚动区顶部为 0，容器底到达滚动区底部为 1
 *   data-scroll="view"   --p：元素顶部进入视口底边为 0，元素底部离开视口顶边为 1
 *   data-scroll="enter"  --p：元素顶部从视口底边走到视口 35% 处，0→1
 *   data-scroll="leave"  --p：元素顶部从滚动区顶边往上移出自身高度，0→1（页头视差用）
 *   data-scroll="tail"   --p：距滚动到底还剩一个元素高度时为 0，到底为 1（幕布式页脚，元素本身 sticky 不动）
 *   data-reveal          元素顶部进入视口 90% 处时加 .in，只触发一次
 *   data-spy="id"        视口中线所在的板块 id 写到 scope 的 data-section 上（导航高亮）
 * scope 自身被写入 --page-p：最近一个滚动容器的整体滚动进度。
 *
 * 监听 scope 上捕获阶段的 scroll（嵌套的 .stage 也能收到）和 window 的 scroll（窄屏整页滚动）；
 * 内容异步渲染（查询返回后）由 MutationObserver 重新收集元素。
 * 系统开启「减弱动态效果」时只处理 reveal（直接显示），不写进度。
 */
export function useScrollScene(scope: RefObject<HTMLElement>) {
  useEffect(() => {
    const root = scope.current;
    if (!root) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let linked: HTMLElement[] = [];
    let reveals = new Set<HTMLElement>();
    let spies: HTMLElement[] = [];
    let frame = 0;
    let lastSection = '';

    const clamp = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
    /**
     * 元素所在的滚动视窗。宽屏是 .stage / .landing；窄屏（≤900px）学生端改由整页文档滚动，
     * .stage 不再产生滚动，这时退回到文档视口。
     */
    const frameOf = (el: HTMLElement) => {
      const box = el.closest('.stage, .landing') as HTMLElement | null;
      if (box && box.scrollHeight > box.clientHeight + 1) {
        const r = box.getBoundingClientRect();
        return { top: r.top, height: r.height, rest: box.scrollHeight - box.scrollTop - box.clientHeight, pos: box.scrollTop, max: box.scrollHeight - box.clientHeight };
      }
      const doc = document.scrollingElement ?? document.documentElement;
      const max = doc.scrollHeight - window.innerHeight;
      return { top: 0, height: window.innerHeight, rest: max - doc.scrollTop, pos: doc.scrollTop, max };
    };

    const collect = () => {
      linked = reduced ? [] : Array.from(root.querySelectorAll<HTMLElement>('[data-scroll]'));
      spies = Array.from(root.querySelectorAll<HTMLElement>('[data-spy]'));
      reveals = new Set(Array.from(root.querySelectorAll<HTMLElement>('[data-reveal]:not(.in)')));
    };

    const update = () => {
      frame = 0;
      const vh = window.innerHeight;

      for (const el of reveals) {
        if (reduced || el.getBoundingClientRect().top < vh * 0.9) {
          el.classList.add('in');
          reveals.delete(el);
        }
      }

      for (const el of linked) {
        const r = el.getBoundingClientRect();
        const sc = frameOf(el);
        let p = 0;
        switch (el.dataset.scroll) {
          case 'pin': {
            const span = r.height - sc.height;
            p = span > 0 ? clamp((sc.top - r.top) / span) : 0;
            break;
          }
          case 'view': p = clamp((vh - r.top) / (vh + r.height)); break;
          case 'enter': p = clamp((vh - r.top) / (vh * 0.65)); break;
          case 'leave': p = clamp((sc.top - r.top) / Math.max(1, r.height)); break;
          case 'tail': p = clamp(1 - sc.rest / Math.max(1, r.height)); break;
        }
        el.style.setProperty('--p', p.toFixed(4));
      }

      const anchor = root.matches('.landing, .stage') ? root : root.querySelector<HTMLElement>('.landing, .stage');
      if (anchor) {
        const f = frameOf(anchor);
        root.style.setProperty('--page-p', f.max > 0 ? clamp(f.pos / f.max).toFixed(4) : '0');
      }

      if (spies.length) {
        let cur = '';
        for (const el of spies) {
          const r = el.getBoundingClientRect();
          if (r.top < vh * 0.5 && r.bottom > vh * 0.5) cur = el.dataset.spy ?? '';
        }
        if (cur !== lastSection) {
          lastSection = cur;
          if (cur) root.dataset.section = cur; else delete root.dataset.section;
        }
      }
    };

    const schedule = () => { if (!frame) frame = requestAnimationFrame(update); };

    collect();
    update();

    let mutFrame = 0;
    const mo = new MutationObserver(() => {
      if (mutFrame) return;
      mutFrame = requestAnimationFrame(() => { mutFrame = 0; collect(); schedule(); });
    });
    mo.observe(root, { childList: true, subtree: true });

    root.addEventListener('scroll', schedule, { capture: true, passive: true });
    // 窄屏下滚动的是文档本身，事件不经过 root
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);

    return () => {
      mo.disconnect();
      cancelAnimationFrame(frame);
      cancelAnimationFrame(mutFrame);
      root.removeEventListener('scroll', schedule, { capture: true });
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
    };
  }, [scope]);
}
