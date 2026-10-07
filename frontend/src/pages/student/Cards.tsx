import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateStudent } from '@/api/students';
import type { Persona } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import { useCards } from '@/hooks/useCards';
import TopBar from '@/components/shell/TopBar';
import PersonaAvatar from '@/components/theme/PersonaAvatar';
import { CARD_ORDER, CARD_QUOTE, CARD_SPOT, PERSONAS, personaByKey, personaFigure, type PersonaKey } from '@/theme/personas';
import dayjs from 'dayjs';

/** 认可卡收藏页：七个卡位落在整层户型图的七个房间上 */
export default function Cards() {
  const student = useStudentStore((s) => s.current)!;
  const setCurrent = useStudentStore((s) => s.setCurrent);
  const qc = useQueryClient();
  const cards = useCards(student.id);
  const [open, setOpen] = useState<PersonaKey | null>(null);
  const base = import.meta.env.BASE_URL;

  const owned = new Map((cards.data?.cards ?? []).map((c) => [c.card_key, c.acquired_at]));
  const unlocked = new Set<string>(cards.data?.unlocked ?? ['leonard']);
  const nextKey = CARD_ORDER.find((k) => !owned.has(k));

  const pick = useMutation({
    mutationFn: (persona: Persona) => updateStudent(student.id, { persona }),
    onSuccess: (s) => { setCurrent(s); qc.invalidateQueries({ queryKey: ['students'] }); toast.info(`${personaByKey(s.persona).name} 现在是你的讲师`); setOpen(null); },
    onError: (e: Error) => toast.error(e.message),
  });

  const current = student.persona ?? 'leonard';
  const sel = open ? personaByKey(open) : null;

  return (
    <>
      <TopBar crumb="认可卡" showSeg={false} />
      <section className="stage">
        <div className="cards">
          <div className="chead">
            <div>
              <h1>认可卡</h1>
              <div className="sub">
                已集齐 {owned.size + 1} / 7 · {nextKey ? `下一张：${personaByKey(nextKey).name}` : '全部集齐'}
              </div>
            </div>
            <div className="hint">卡怎么来的不公开。越努力，越快。</div>
          </div>

          <div className="floor">
            <img src={`${base}tbbt/apartment/floorplan-render-light.jpg`} alt="" draggable={false} />
            {PERSONAS.map((p) => {
              const key = p.key as PersonaKey;
              const spot = CARD_SPOT[key];
              const has = key === 'leonard' || owned.has(key);
              const isNext = key === nextKey;
              return (
                <button
                  type="button"
                  key={key}
                  className={`spot ${has ? 'has' : 'no'} ${isNext ? 'next' : ''} ${current === key ? 'cur' : ''}`}
                  style={{ left: `${spot.x}%`, top: `${spot.y}%`, ['--pc' as string]: p.color }}
                  onClick={() => setOpen(key)}
                  title={has ? `${p.name} · ${spot.room}` : `第 ${CARD_ORDER.indexOf(key) + 1} 张认可卡`}
                >
                  <PersonaAvatar persona={key} size={44} locked={!has} />
                  <span className="lbl">{has ? p.name : '?'}</span>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {sel && (
        <div className="cmodal" onClick={() => setOpen(null)}>
          <div className={`ccard ${unlocked.has(sel.key) ? '' : 'locked'}`} style={{ ['--pc' as string]: sel.color }} onClick={(e) => e.stopPropagation()}>
            <div className="art">
              <img src={personaFigure(sel.key as PersonaKey)} alt="" className={unlocked.has(sel.key) ? '' : 'sil'} />
            </div>
            <div className="txt">
              <div className="kicker">{CARD_SPOT[sel.key as PersonaKey].room}</div>
              <h2>{unlocked.has(sel.key) ? sel.name : `第 ${CARD_ORDER.indexOf(sel.key as PersonaKey) + 1} 张认可卡`}</h2>
              {unlocked.has(sel.key) ? (
                <>
                  <p className="quote">"{CARD_QUOTE[sel.key as PersonaKey]}"</p>
                  <div className="meta">
                    {sel.key === 'leonard' ? '注册即有' : `${dayjs(owned.get(sel.key as Persona)).format('YYYY 年 M 月 D 日')} 获得`} · {sel.tone}
                  </div>
                  <div className="acts">
                    {current === sel.key
                      ? <span className="on">当前讲师</span>
                      : <button type="button" className="btn pri" disabled={pick.isPending} onClick={() => pick.mutate(sel.key as Persona)}>选为讲师</button>}
                    <button type="button" className="btn ghost" onClick={() => setOpen(null)}>关闭</button>
                  </div>
                </>
              ) : (
                <>
                  <p className="quote muted">还没有人认可你到这一步。</p>
                  <div className="meta">继续练、继续问，卡会自己来。</div>
                  <div className="acts"><button type="button" className="btn ghost" onClick={() => setOpen(null)}>关闭</button></div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
