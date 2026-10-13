import { useLayoutEffect, useRef } from 'react';
import { gsap } from 'gsap';

/**
 * 数字进入视口时从 0 滚到目标值。span 不放 React 子节点，文本只由这里写，
 * 避免 GSAP 改写 React 管理的文本节点。
 */
export default function CountUp({ value, duration = 1.4, delay = 0.25 }: { value: number; duration?: number; delay?: number }) {
  const ref = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.textContent = String(value);
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const o = { v: 0 };
    el.textContent = '0';
    const tween = gsap.to(o, {
      v: value, duration, delay, ease: 'power3.out', paused: true,
      onUpdate: () => { el.textContent = String(Math.round(o.v)); },
    });
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      tween.play();
      io.disconnect();
    }, { rootMargin: '0px 0px -12% 0px' });
    io.observe(el);
    return () => { io.disconnect(); tween.kill(); el.textContent = String(value); };
  }, [value, duration, delay]);

  return <span ref={ref} className="count-up" />;
}
