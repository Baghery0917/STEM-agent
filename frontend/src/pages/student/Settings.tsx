import { useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import { updateStudent } from '@/api/students';
import type { ExplainStyle, Persona } from '@/api/types';
import { PERSONAS, DEFAULT_PERSONA } from '@/theme/personas';
import PersonaAvatar from '@/components/theme/PersonaAvatar';
import { useCards } from '@/hooks/useCards';
import { CARD_ORDER, type PersonaKey } from '@/theme/personas';
import { useStudentStore } from '@/stores/studentStore';
import { useUiStore } from '@/stores/uiStore';
import { toast } from '@/stores/toastStore';
import TopBar from '@/components/shell/TopBar';
import { GENDER_LABEL } from '@/utils/enums';
import ChapterHero from '@/components/theme/ChapterHero';
import SceneSection from '@/components/theme/SceneSection';
import { gsap, onEnter, riseHeroTitle, useSmoothStage, useStageMotion } from '@/hooks/useStageMotion';

/** 手写签名笔迹，viewBox 0 0 260 80；第二段是收尾下划线 */
const SIGN_RESIDENT = [
  'M14 52 C 22 22, 40 12, 38 34 C 36 52, 22 60, 30 48 C 40 34, 52 28, 56 40 C 60 52, 50 58, 62 50 C 74 42, 78 26, 88 30 C 96 34, 86 54, 98 52 C 112 50, 116 30, 126 34 C 134 38, 128 54, 140 50 C 152 46, 160 36, 170 40 C 178 44, 174 56, 186 52 C 198 48, 206 38, 218 42',
  'M30 66 C 90 60, 170 62, 238 56',
];
const SIGN_SHELDON = [
  'M20 44 C 30 16, 58 14, 50 32 C 44 46, 22 46, 30 58 C 38 68, 60 60, 66 44 C 70 34, 70 22, 76 22 C 80 22, 74 48, 76 56 C 80 42, 88 36, 94 42 C 98 48, 94 56, 102 54 C 112 52, 114 38, 124 40 C 132 42, 126 56, 136 54 C 146 52, 150 30, 156 20 C 160 30, 154 52, 162 54 C 172 56, 178 40, 188 42 C 196 44, 192 56, 202 54 C 214 52, 222 40, 236 36',
  'M40 70 C 100 62, 160 72, 226 64 C 232 63, 236 66, 230 68',
];

const STYLES: { value: ExplainStyle | null; label: string }[] = [
  { value: 'direct', label: '直接给答案' },
  { value: 'guided', label: '引导我自己找' },
  { value: 'hint', label: '只给提示' },
];

export default function Settings() {
  const student = useStudentStore((s) => s.current)!;
  const setCurrent = useStudentStore((s) => s.setCurrent);
  const ui = useUiStore();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const personaMutation = useMutation({
    mutationFn: (persona: Persona) => updateStudent(student.id, { persona }),
    onSuccess: (s) => { setCurrent(s); qc.invalidateQueries({ queryKey: ['students'] }); toast.info('讲师已切换，对新会话生效'); },
    onError: (e: Error) => toast.error(e.message),
  });
  const currentPersona = student.persona ?? DEFAULT_PERSONA;
  const cards = useCards(student.id);
  const unlocked = new Set<string>(cards.data?.unlocked ?? ['leonard']);

  const stageRef = useRef<HTMLElement>(null);
  useSmoothStage(stageRef);
  useStageMotion(stageRef, ({ root, scroller }) => {
    riseHeroTitle(root);
    // 每条条款进入视口时，行从左侧依次写入
    root.querySelectorAll<HTMLElement>('.settings-chapter .scene-section').forEach((sec) => {
      gsap.from(sec.querySelectorAll('.srow'), {
        x: -18, autoAlpha: 0, duration: 0.7, ease: 'power3.out', stagger: 0.08, delay: 0.15, clearProps: 'transform,opacity,visibility',
        scrollTrigger: onEnter(sec, scroller, 'top 88%'),
      });
    });
    // 签名区：两个人先后落笔，最后盖生效章
    const sign = root.querySelector<HTMLElement>('.agreement-sign');
    if (!sign) return;
    const [resident, sheldon] = Array.from(sign.querySelectorAll('.sign-pad'));
    gsap.timeline({ scrollTrigger: onEnter(sign, scroller, 'top 85%') })
      .from(resident.querySelectorAll('path'), { drawSVG: 0, duration: 1.1, ease: 'power1.inOut', stagger: 0.9 }, 0.2)
      .from(resident.querySelector('figcaption'), { autoAlpha: 0, y: 6, duration: 0.4 }, '-=0.4')
      .from(sheldon.querySelectorAll('path'), { drawSVG: 0, duration: 1.1, ease: 'power1.inOut', stagger: 0.9 }, '-=0.1')
      .from(sheldon.querySelector('figcaption'), { autoAlpha: 0, y: 6, duration: 0.4 }, '-=0.4')
      .from(sign.querySelector('.sign-seal'), { scale: 2, rotate: -40, autoAlpha: 0, duration: 0.55, ease: 'back.out(2.4)' }, '-=0.1');
  }, []);

  const styleMutation = useMutation({
    mutationFn: (explain_style: ExplainStyle | null) => updateStudent(student.id, { explain_style }),
    onSuccess: (s) => { setCurrent(s); qc.invalidateQueries({ queryKey: ['students'] }); toast.info('讲解风格已更新'); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <>
      <TopBar crumb="设置" showSeg={false} back />
      <section className="stage" ref={stageRef}>
        <div className="settings settings-chapter">
          <ChapterHero
            chapter="04"
            eyebrow="Roommate Agreement"
            title="把学习习惯写进室友协议。"
            description="这里的条款只决定你如何被讲解、被提醒和被陪伴。随时可以改，下一次会话就会生效。"
            art={`${import.meta.env.BASE_URL}tbbt/illustrations/apartment-isometric.jpg`}
            artAlt="Apartment 4A 客厅等距插画"
          />
          <SceneSection number="4A.1" eyebrow="Resident file" title="住户档案" aside="身份与会话入口">
            <div className="srow">
              <div className="avatar" style={{ width: 40, height: 40, fontSize: 15 }}>{student.name.slice(0, 1)}</div>
              <div><div className="t">{student.name}</div><div className="d">{GENDER_LABEL[student.gender]} · 学号 #{student.id}</div></div>
              <button type="button" className="btn ctl" onClick={() => { setCurrent(null); navigate('/login'); }}>切换学生</button>
            </div>
          </SceneSection>
          <SceneSection number="4A.2" eyebrow="Learning protocol" title="讲解条款" aside="新会话生效">
            <div className="srow">
              <div><div className="t">讲解风格</div><div className="d">默认由教学策略模块决定，你可以手动覆盖</div></div>
              <div className="ctl radio">
                <button type="button" className={student.explain_style == null ? 'on' : ''} onClick={() => styleMutation.mutate(null)}>自动</button>
                {STYLES.map((s) => (
                  <button type="button" key={s.label} className={student.explain_style === s.value ? 'on' : ''} onClick={() => styleMutation.mutate(s.value)}>{s.label}</button>
                ))}
              </div>
            </div>
          </SceneSection>
          <SceneSection number="4A.3" eyebrow="Tutor seat" title="谁坐在你对面" aside="认可卡解锁新讲师">
            <div className="srow persona-row">
              <div><div className="t">讲师</div><div className="d">只换语气，不换教法。切换对新会话生效。</div></div>
              <div className="ctl persona-pick">
                {PERSONAS.map((p) => {
                  const locked = !unlocked.has(p.key);
                  const idx = CARD_ORDER.indexOf(p.key as PersonaKey) + 1;
                  return (
                    <button
                      type="button"
                      key={p.key}
                      className={`${currentPersona === p.key ? 'on' : ''} ${locked ? 'locked' : ''}`}
                      title={locked ? `第 ${idx} 张认可卡解锁` : `${p.name} · ${p.tone}`}
                      disabled={personaMutation.isPending || locked}
                      onClick={() => personaMutation.mutate(p.key)}
                    >
                      <PersonaAvatar persona={p.key} size={40} locked={locked} />
                      <span className="nm">{locked ? `第 ${idx} 张` : p.name}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="srow persona-desc">
              <PersonaAvatar persona={currentPersona} size={28} />
              <div>
                <div className="t">{PERSONAS.find((p) => p.key === currentPersona)!.name}</div>
                <div className="d">{PERSONAS.find((p) => p.key === currentPersona)!.tone} · <i>{PERSONAS.find((p) => p.key === currentPersona)!.tagline}</i></div>
              </div>
            </div>
          </SceneSection>
          <SceneSection number="4A.4" eyebrow="Thermostat · 71°F" title="学习状态感知" aside="画面不上传、不保存">
            <div className="srow">
              <div><div className="t">情绪识别</div><div className="d">使用摄像头判断学习状态，只用来调整讲解节奏，画面不上传不保存</div></div>
              <button type="button" className={`toggle ctl ${ui.cameraEnabled ? 'on' : ''}`} onClick={() => ui.setCameraEnabled(!ui.cameraEnabled)} aria-label="情绪识别" />
            </div>
          </SceneSection>
          <footer className="agreement-sign" data-reveal>
            <div className="scene-kicker"><span>4A.5</span>Signatures</div>
            <h2>双方签字，条款生效。</h2>
            <p>改条款不用重签，下一次会话自动按新条款执行。</p>
            <div className="sign-row">
              <figure className="sign-pad">
                <svg viewBox="0 0 260 80" aria-hidden="true">{SIGN_RESIDENT.map((d) => <path key={d} d={d} />)}</svg>
                <figcaption><b>{student.name}</b><span>住户 · 学号 #{student.id}</span></figcaption>
              </figure>
              <figure className="sign-pad">
                <svg viewBox="0 0 260 80" aria-hidden="true">{SIGN_SHELDON.map((d) => <path key={d} d={d} />)}</svg>
                <figcaption><b>Sheldon Cooper</b><span>主租户 · 协议起草人</span></figcaption>
              </figure>
              <div className="sign-seal" aria-label={`生效日期 ${dayjs().format('YYYY.MM.DD')}`}>
                <span>Effective</span><b>{dayjs().format('MM.DD')}</b><span>{dayjs().format('YYYY')}</span>
              </div>
            </div>
          </footer>
        </div>
      </section>
    </>
  );
}
