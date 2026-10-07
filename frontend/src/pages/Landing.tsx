import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import BrandMark from '@/components/theme/BrandMark';
import { PHYSICS_NEWS, TBBT_TRIVIA } from '@/theme/landing';
import { PERSONAS, personaFigure, type PersonaKey } from '@/theme/personas';
import { useStudentStore } from '@/stores/studentStore';
import { useReveal } from '@/hooks/useReveal';

const WORD = 'STEM AGENT';
const ROWS = 9;

/**
 * 落地页：长滚动，三个板块。
 * 01 大字墙：九行 STEM AGENT 循环滚动，中间一行实心，其余描边；鼠标位置决定哪一行「亮」。
 * 02 物理界的新闻：静态列表。
 * 03 生活大爆炸冷知识：横向卡片。
 */
export default function Landing() {
  const navigate = useNavigate();
  const student = useStudentStore((s) => s.current);
  const root = useRef<HTMLDivElement>(null);
  const [hot, setHot] = useState(Math.floor(ROWS / 2));
  const [scrolled, setScrolled] = useState(false);
  useReveal(root);

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

  const goLogin = () => navigate(student ? '/teaching' : '/login');
  const base = import.meta.env.BASE_URL;

  return (
    <div className="agent">
      <div className="landing" ref={root}>
        <header className={`land-nav ${scrolled ? 'scrolled' : ''}`}>
          <a className="land-brand" href="#top" onClick={(e) => { e.preventDefault(); root.current?.scrollTo({ top: 0, behavior: 'smooth' }); }}>
            <BrandMark size={28} />
            <span className="wordmark"><span className="w1">STEM</span><span className="w2">Agent</span></span>
          </a>
          <nav className="land-links">
            <a href="#news">News</a>
            <a href="#trivia">Trivia</a>
            <a href="#tutors">Tutors</a>
          </nav>
          <button type="button" className="land-login" onClick={goLogin}>
            <span>{student ? `回到 4A · ${student.name}` : 'Login'}</span>
            <i>→</i>
          </button>
        </header>

        <section className="land-hero" id="top" onMouseMove={onMove} onMouseLeave={() => setHot(Math.floor(ROWS / 2))}>
          <div className="wall" aria-hidden="true">
            {Array.from({ length: ROWS }).map((_, i) => (
              <div key={i} className={`row ${i === hot ? 'hot' : ''} ${i % 2 ? 'rev' : ''}`} style={{ ['--i' as string]: i }}>
                <span>{Array.from({ length: 6 }).map(() => WORD).join('  ·  ')}&nbsp;&nbsp;·&nbsp;&nbsp;</span>
                <span>{Array.from({ length: 6 }).map(() => WORD).join('  ·  ')}&nbsp;&nbsp;·&nbsp;&nbsp;</span>
              </div>
            ))}
          </div>
          <div className="hero-copy" data-reveal>
            <div className="eyebrow">Apartment 4A · Pasadena</div>
            <h1>你好，我是 <em>STEM Agent</em>。</h1>
            <p>一个有七位讲师的物理教学系统。他们教法相同，只是语气不同。你从 Leonard 开始，一路把其余六个人的认可卡拿到手。</p>
            <div className="hero-acts">
              <button type="button" className="btn pri big" onClick={goLogin}>敲门进入 ↵</button>
              <a className="btn ghost big" href="#news">先看看楼下 ↓</a>
            </div>
          </div>
          <div className="hero-foot">
            <span>(scroll to explore)</span>
            <span>{dayjs().format('YYYY.MM.DD')}</span>
          </div>
        </section>

        <section className="land-sec" id="news">
          <div className="sec-head" data-reveal>
            <div className="num">01</div>
            <div>
              <div className="kicker">What's new in physics</div>
              <h2>物理界的新闻</h2>
            </div>
            <p className="lede">每周手动更新几条。不求全，只挑能在课上讲清楚的。</p>
          </div>
          <ol className="news-list">
            {PHYSICS_NEWS.map((n, i) => (
              <li key={n.title} data-reveal style={{ ['--d' as string]: `${i * 60}ms` }}>
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

        <section className="land-sec trivia" id="trivia">
          <div className="sec-head" data-reveal>
            <div className="num">02</div>
            <div>
              <div className="kicker">Things you didn't know about 4A</div>
              <h2>生活大爆炸冷知识</h2>
            </div>
            <p className="lede">一部分来自剧集，一部分来自科学顾问的访谈，有几条是我们自己从全剧台词里数出来的。</p>
          </div>
          <div className="trivia-track">
            {TBBT_TRIVIA.map((t, i) => (
              <article key={t.head} className="trivia-card" data-reveal style={{ ['--d' as string]: `${(i % 4) * 70}ms` }}>
                <div className="idx">{String(i + 1).padStart(2, '0')}</div>
                <h3>{t.head}</h3>
                <p>{t.body}</p>
                <div className="ref">{t.ref}</div>
              </article>
            ))}
          </div>
        </section>

        <section className="land-sec tutors" id="tutors">
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
              <figure key={p.key} className="tutor-card" data-reveal style={{ ['--pc' as string]: p.color, ['--d' as string]: `${i * 50}ms` }}>
                <img src={personaFigure(p.key as PersonaKey)} alt={p.name} loading="lazy" />
                <figcaption>
                  <b>{p.name}</b>
                  <span>{p.tagline}</span>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>

        <footer className="land-foot">
          <div className="foot-big" data-reveal>
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
