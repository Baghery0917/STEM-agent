import { useLayoutEffect, useRef, type DependencyList, type RefObject } from 'react';
import Lenis from 'lenis';
import 'lenis/dist/lenis.css';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { SplitText } from 'gsap/SplitText';
import { DrawSVGPlugin } from 'gsap/DrawSVGPlugin';

gsap.registerPlugin(ScrollTrigger, SplitText, DrawSVGPlugin);

/** 和 global.css 的窄屏断点一致：≤900px 时 .stage 不再滚动，改由文档滚动 */
const WIDE = '(min-width: 901px)';
export const MOTION = '(prefers-reduced-motion: no-preference)';

export interface StageMotion {
  /** ScrollTrigger 的 scroller：宽屏是 .stage，窄屏是 window */
  scroller: HTMLElement | Window;
  root: HTMLElement;
}

/**
 * 章节页（沙发周报 / 公寓钥匙 / 室友协议）的平滑滚动：Lenis 接管滚动容器的滚轮惯性，
 * 由 GSAP ticker 驱动并通知 ScrollTrigger。Lenis 写的是原生 scrollTop，useScrollScene 照常工作。
 * 系统开启「减弱动态效果」时不启用。
 */
export function useSmoothStage(stage: RefObject<HTMLElement>, deps: DependencyList = []) {
  const lenisRef = useRef<Lenis | null>(null);
  useLayoutEffect(() => {
    const el = stage.current;
    if (!el) return;
    const mm = gsap.matchMedia();
    mm.add({ wide: WIDE, motion: MOTION }, (ctx) => {
      if (!ctx.conditions?.motion) return;
      // allowNestedScroll：电梯井道、公式、代码块等内层滚动区照常原生滚动
      const opts = { autoRaf: false, lerp: 0.11, allowNestedScroll: true };
      const lenis = new Lenis(ctx.conditions.wide ? { ...opts, wrapper: el, content: el.firstElementChild ?? el } : opts);
      lenisRef.current = lenis;
      const tick = (t: number) => lenis.raf(t * 1000);
      lenis.on('scroll', ScrollTrigger.update);
      gsap.ticker.add(tick);
      gsap.ticker.lagSmoothing(0);

      // 内容异步渲染、图片加载会改变高度，触发位置要跟着重算
      let frame = 0;
      const ro = new ResizeObserver(() => {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => ScrollTrigger.refresh());
      });
      Array.from(el.children).forEach((c) => ro.observe(c));

      return () => {
        ro.disconnect();
        cancelAnimationFrame(frame);
        gsap.ticker.remove(tick);
        gsap.ticker.lagSmoothing(500, 33);
        lenis.destroy();
        lenisRef.current = null;
      };
    });
    return () => mm.revert();
    // stage 元素可能随页面状态替换（如新对话 → 会话），deps 让 Lenis 重新绑定
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, ...deps]);
  return lenisRef;
}

/**
 * 在 gsap.matchMedia 里执行 build；其中创建的 tween、ScrollTrigger、SplitText
 * 在 deps 变化、断点切换、卸载时一并还原。减弱动态效果时不执行。
 */
export function useStageMotion(stage: RefObject<HTMLElement>, build: (m: StageMotion) => void | (() => void), deps: DependencyList) {
  const buildRef = useRef(build);
  buildRef.current = build;

  useLayoutEffect(() => {
    const el = stage.current;
    if (!el) return;
    const mm = gsap.matchMedia(el);
    mm.add({ wide: WIDE, motion: MOTION }, (ctx) => {
      if (!ctx.conditions?.motion) return;
      return buildRef.current({ scroller: ctx.conditions.wide ? el : window, root: el });
    });
    return () => mm.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, ...deps]);
}

/** 弹窗卡片翻面入场（替代 CSS 的 float-in），deps 变化即重放 */
export function useFlipIn(card: RefObject<HTMLElement>, deps: DependencyList) {
  useLayoutEffect(() => {
    const el = card.current;
    if (!el) return;
    const mm = gsap.matchMedia();
    mm.add(MOTION, () => {
      gsap.fromTo(el,
        { rotationY: -70, scale: 0.86, autoAlpha: 0, transformPerspective: 1000 },
        { rotationY: 0, scale: 1, autoAlpha: 1, duration: 0.75, ease: 'back.out(1.4)', clearProps: 'transform' });
    });
    return () => mm.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

/** 进入视口触发一次的 ScrollTrigger 配置 */
export function onEnter(trigger: Element, scroller: HTMLElement | Window, start = 'top 82%'): ScrollTrigger.Vars {
  return { trigger, scroller, start, once: true };
}

/**
 * 章节页大标题逐字升起。中文没有空格分词，按字拆（按行拆会把整段当成一个不换行的词）。
 * 标题内容是静态的，SplitText 替换掉 React 的文本节点不会和后续渲染冲突。
 */
export function riseHeroTitle(root: HTMLElement) {
  const h1 = root.querySelector('.chapter-hero h1');
  if (!h1) return;
  const split = SplitText.create(h1, { type: 'chars', charsClass: 'hero-char' });
  gsap.from(split.chars, {
    yPercent: 70, rotate: 8, autoAlpha: 0, duration: 0.9, ease: 'expo.out', stagger: 0.035, delay: 0.12,
  });
}

/** 新出现的元素（消息、题卡）入场：只对还没播过的 el 播一次 */
const played = new WeakSet<Element>();
export function enterOnce(els: Iterable<Element>, vars: gsap.TweenVars) {
  const fresh = Array.from(els).filter((el) => !played.has(el));
  if (!fresh.length || !window.matchMedia(MOTION).matches) { fresh.forEach((el) => played.add(el)); return; }
  fresh.forEach((el) => played.add(el));
  gsap.from(fresh, { clearProps: 'transform,opacity,visibility,filter', ...vars });
}

/** 标记为已播放但不播：流式输出过的内容已经"逐字出现"过，不要再整段浮现一次 */
export function markPlayed(els: Iterable<Element>) {
  for (const el of els) played.add(el);
}

/** 正确作答的小礼花：从 origin 中心向外喷出几粒圆点 */
export function burst(origin: Element, colors: string[]) {
  if (!window.matchMedia(MOTION).matches) return;
  const r = origin.getBoundingClientRect();
  const layer = document.createElement('div');
  layer.className = 'burst-layer';
  layer.style.left = `${r.left + r.width / 2}px`;
  layer.style.top = `${r.top + r.height / 2}px`;
  document.body.appendChild(layer);
  const dots = Array.from({ length: 14 }, (_, i) => {
    const d = document.createElement('i');
    d.style.background = colors[i % colors.length];
    layer.appendChild(d);
    return d;
  });
  gsap.timeline({ onComplete: () => layer.remove() })
    .to(dots, {
      x: () => gsap.utils.random(-70, 70), y: () => gsap.utils.random(-70, 30), scale: () => gsap.utils.random(0.6, 1.4),
      duration: 0.7, ease: 'expo.out',
    })
    .to(dots, { y: '+=36', autoAlpha: 0, duration: 0.5, ease: 'power1.in' }, 0.45);
}

export { gsap, ScrollTrigger, SplitText };
