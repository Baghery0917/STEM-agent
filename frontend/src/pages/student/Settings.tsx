import { useMutation, useQueryClient } from '@tanstack/react-query';
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

  const styleMutation = useMutation({
    mutationFn: (explain_style: ExplainStyle | null) => updateStudent(student.id, { explain_style }),
    onSuccess: (s) => { setCurrent(s); qc.invalidateQueries({ queryKey: ['students'] }); toast.info('讲解风格已更新'); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <>
      <TopBar crumb="设置" showSeg={false} />
      <section className="stage">
        <div className="settings">
          <h1>设置</h1>
          <div className="card"><div className="bd" style={{ padding: '4px 18px' }}>
            <div className="srow">
              <div className="avatar" style={{ width: 40, height: 40, fontSize: 15 }}>{student.name.slice(0, 1)}</div>
              <div><div className="t">{student.name}</div><div className="d">{GENDER_LABEL[student.gender]} · 学号 #{student.id}</div></div>
              <button type="button" className="btn ctl" onClick={() => { setCurrent(null); navigate('/login'); }}>切换学生</button>
            </div>
            <div className="srow">
              <div><div className="t">讲解风格</div><div className="d">默认由教学策略模块决定，你可以手动覆盖</div></div>
              <div className="ctl radio">
                <button type="button" className={student.explain_style == null ? 'on' : ''} onClick={() => styleMutation.mutate(null)}>自动</button>
                {STYLES.map((s) => (
                  <button type="button" key={s.label} className={student.explain_style === s.value ? 'on' : ''} onClick={() => styleMutation.mutate(s.value)}>{s.label}</button>
                ))}
              </div>
            </div>
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
            <div className="srow">
              <div><div className="t">情绪识别</div><div className="d">使用摄像头判断学习状态，只用来调整讲解节奏，画面不上传不保存</div></div>
              <button type="button" className={`toggle ctl ${ui.cameraEnabled ? 'on' : ''}`} onClick={() => ui.setCameraEnabled(!ui.cameraEnabled)} aria-label="情绪识别" />
            </div>
          </div></div>
        </div>
      </section>
    </>
  );
}
