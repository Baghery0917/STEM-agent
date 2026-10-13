import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listPublicNews } from '@/api/news';
import dayjs from 'dayjs';
import BrandMark from '@/components/theme/BrandMark';
import { PHYSICS_NEWS, TBBT_TRIVIA } from '@/theme/landing';
import { PERSONAS, personaFigure, type PersonaKey } from '@/theme/personas';
import { useScrollScene } from '@/hooks/useScrollScene';

const WORD = 'STEM AGENT';
const ROWS = 9;
/** 宣言逐词点亮：按词切分，标点跟随前一个词 */
const STATEMENT = '七位 讲师， 教法 相同， 只是 语气 不同。 你从 Leonard 开始， 一路 把 其余 六个人 的 认可卡 拿到手。';
/** 讲师卡视差速度（px），相邻卡错开，避免整排同步移动 */
const TUTOR_SPEED = [40, 96, 18, 72, 30, 110, 54];
const SECTIONS = [
  { id: 'news', label: 'News' },
  { id: 'trivia', label: 'Trivia' },
  { id: 'tutors', label: 'Tutors' },
];

/**
 * 落地页：长滚动叙事。滚动效果全部由 useScrollScene 写 CSS 变量驱动，滚动期间不重渲染。
 * 开场  大字墙固定在视口里，滚动时九行向两侧拉开、整体放大淡出，标题卡后退
 * 宣言  固定居中的一句话，随滚动逐词点亮
 * 01    物理新闻：左侧标题吸顶，右侧条目进入视口时依次划线展开
 * 02    冷知识：纵向滚动驱动横向卡片轨道（窄屏退回原生横滑 + 吸附）
 * 03    讲师：七张卡不同速度视差，背景大字横移
 * 页脚  幕布式：内容层滚走后露出固定在底部的页脚
 */
export default function Landing() {
  const navigate = useNavigate();
  const root = useRef<HTMLDivElement>(null);
  const [hot, setHot] = useState(Math.floor(ROWS / 2));
  const [scrolled, setScrolled] = useState(false);
  const newsQuery = useQuery({ queryKey: ['public-news'], queryFn: () => listPublicNews(8), staleTime: 300_000, retry: 0 });
  const news = newsQuery.data?.length ? newsQuery.data.map((n) => ({ date: n.published_on, tag: n.tag, title: n.title, summary: n.summary, source: n.source, url: n.url })) : PHYSICS_NEWS;
  useScrollScene(root);

  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const onScroll = () => setScrolled(el.scrollTop > 40);
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const i = Math.min(ROWS - 1, Math.max(0, Math.floor(((e.clientY - r.top) / r.height) * ROWS)));
    setHot(i);
  };

  // 预览构建用 hash 路由，锚点 href 会被当成路由；统一改为容器内平滑滚动
  const jump = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    const scroller = root.current;
    if (!scroller) return;
    if (id === 'top') { scroller.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    const el = scroller.querySelector<HTMLElement>(`#${id}`);
    if (el) scroller.scrollTo({ top: el.offsetTop - (id === 'news' ? 72 : 0), behavior: 'smooth' });
  };

  const goLogin = () => navigate('/login');
  const base = import.meta.env.BASE_URL;
  const words = STATEMENT.split(' ');

  return (
    <div className="agent">
      <div className="landing" ref={root}>
        <header className={`land-nav ${scrolled ? 'scrolled' : ''}`}>
          <a className="land-brand" href="#top" onClick={jump('top')}>
            <BrandMark size={28} />
            <span className="wordmark"><span className="w1">STEM</span><span className="w2">Agent</span></span>
          </a>
          <nav className="land-links">
            {SECTIONS.map((s) => (
              <a key={s.id} href={`#${s.id}`} data-for={s.id} onClick={jump(s.id)}>{s.label}</a>
            ))}
          </nav>
          <button type="button" className="land-login" onClick={goLogin}>
            <span>Login</span>
            <i>→</i>
          </button>
          <span className="land-progress" aria-hidden="true" />
        </header>

        <div className="land-main">
          <div className="hero-pin" data-scroll="pin" id="top">
            <section className="land-hero" onMouseMove={onMove} onMouseLeave={() => setHot(Math.floor(ROWS / 2))}>
              <div className="wall" aria-hidden="true">
                {Array.from({ length: ROWS }).map((_, i) => (
                  <div key={i} className="row-shift" style={{ ['--i' as string]: i, ['--dir' as string]: i % 2 ? 1 : -1, ['--far' as string]: Math.abs(i - Math.floor(ROWS / 2)) }}>
                    <div className={`row ${i === hot ? 'hot' : ''} ${i % 2 ? 'rev' : ''}`}>
                      <span>{Array.from({ length: 6 }).map(() => WORD).join('  ·  ')}&nbsp;&nbsp;·&nbsp;&nbsp;</span>
                      <span>{Array.from({ length: 6 }).map(() => WORD).join('  ·  ')}&nbsp;&nbsp;·&nbsp;&nbsp;</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="hero-copy">
                <div className="eyebrow">Apartment 4A · Pasadena</div>
                <h1><span className="ln">你好，我是</span> <em className="ln">STEM Agent</em><span className="ln">。</span></h1>
                <p>一个有七位讲师的物理教学系统。</p>
                <div className="hero-acts">
                  <button type="button" className="btn pri big" onClick={goLogin}>敲门进入 ↵</button>
                  <a className="btn ghost big" href="#news" onClick={jump('news')}>先看看楼下 ↓</a>
                </div>
              </div>
              <div className="hero-foot">
                <span className="cue"><i />scroll to explore</span>
                <span>{dayjs().format('YYYY.MM.DD')}</span>
              </div>
            </section>
          </div>

          <div className="statement-pin" data-scroll="pin">
            <div className="statement">
              <p style={{ ['--n' as string]: words.length }}>
                {words.map((w, i) => (
                  <span key={i} className={w === 'Leonard' ? 'em' : ''} style={{ ['--i' as string]: i }}>{w}</span>
                ))}
              </p>
            </div>
          </div>

          <section className="land-sec news" id="news" data-spy="news">
            <div className="sec-head" data-reveal>
              <div className="num">01</div>
              <div>
                <div className="kicker">What's new in physics</div>
                <h2>物理界的新闻</h2>
              </div>
              <p className="lede">在管理台更新。不求全，只挑能在课上讲清楚的。</p>
            </div>
            <ol className="news-list">
              {news.map((n, i) => (
                <li key={n.title} data-reveal style={{ ['--d' as string]: `${(i % 3) * 80}ms` }}>
                  <a href={n.url} target="_blank" rel="noreferrer">
                    <div className="meta">
                      <span className="tag">{n.tag}</span>
                      <time>{dayjs(n.date).format('M 月 D 日')}</time>
                    </div>
                    <div className="body">
                      <h3>{n.title}</h3>
                      <p>{n.summary}</p>
                    </div>
                    <div className="src">{n.source} <i>↗</i></div>
                  </a>
                </li>
              ))}
            </ol>
          </section>

          <section className="trivia-pin" id="trivia" data-scroll="hpin" data-spy="trivia">
            <div className="trivia-stick">
              <div className="sec-head" data-reveal>
                <div className="num">02</div>
                <div>
                  <div className="kicker">Things you didn't know about 4A</div>
                  <h2>生活大爆炸冷知识</h2>
                </div>
                <p className="lede">一部分来自剧集，一部分来自科学顾问的访谈，有几条是我们自己从全剧台词里数出来的。</p>
              </div>
              <div className="trivia-track" data-htrack>
                <div className="trivia-rail">
                  {TBBT_TRIVIA.map((t, i) => (
                    <article key={t.head} className="trivia-card" data-reveal style={{ ['--d' as string]: `${(i % 4) * 70}ms`, ['--k' as string]: i / (TBBT_TRIVIA.length - 1) }}>
                      <div className="idx">{String(i + 1).padStart(2, '0')}</div>
                      <h3>{t.head}</h3>
                      <p>{t.body}</p>
                      <div className="ref">{t.ref}</div>
                    </article>
                  ))}
                </div>
              </div>
              <div className="trivia-meter" aria-hidden="true">
                <span>01</span><i><b /></i><span>{String(TBBT_TRIVIA.length).padStart(2, '0')}</span>
              </div>
            </div>
          </section>

          <section className="land-sec tutors" id="tutors" data-scroll="view" data-spy="tutors">
            <div className="tutors-bg" aria-hidden="true">Seven tutors · one method · Seven tutors · one method</div>
            <div className="sec-head" data-reveal>
              <div className="num">03</div>
              <div>
                <div className="kicker">Seven tutors, one method</div>
                <h2>谁来给你讲题</h2>
              </div>
              <p className="lede">同一道题，七种讲法。口头禅全部来自剧中台词，带集号可查。</p>
            </div>
            <div className="tutor-row">
              {PERSONAS.map((p, i) => (
                <div key={p.key} className="tutor-slot" style={{ ['--speed' as string]: TUTOR_SPEED[i] }}>
                  <figure className="tutor-card" data-reveal style={{ ['--pc' as string]: p.color, ['--d' as string]: `${i * 60}ms` }}>
                    <img src={personaFigure(p.key as PersonaKey)} alt={p.name} loading="lazy" />
                    <figcaption>
                      <b>{p.name}</b>
                      <span>{p.tagline}</span>
                    </figcaption>
                  </figure>
                </div>
              ))}
            </div>
          </section>
        </div>

        <footer className="land-foot" data-scroll="tail">
          <div className="foot-big">
            <span>Knock,</span><span>knock,</span><span>knock.</span>
          </div>
          <div className="foot-row">
            <button type="button" className="btn pri big" onClick={goLogin}>敲门进入 ↵</button>
            <div className="foot-meta">
              <span>STEM Agent · 物理教学系统</span>
              <span>素材来自《生活大爆炸》粉丝社区，仅作内部演示</span>
            </div>
          </div>
          <img className="foot-art" src={`${base}tbbt/backgrounds/four-heads-yellow.jpg`} alt="" loading="lazy" />
        </footer>
      </div>
    </div>
  );
}
