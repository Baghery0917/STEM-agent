import { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createStudent, listStudents } from '@/api/students';
import { adminLogin } from '@/api/admin';
import type { Gender, StudentResponse } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import Toasts from '@/components/shell/Toasts';
import { GENDER_OPTIONS } from '@/utils/enums';
import { LOGIN } from '@/theme/copy';
import BrandMark from '@/components/theme/BrandMark';
import WeekdayIcon from '@/components/theme/WeekdayIcon';
import { todayTheme } from '@/theme/weekday';
import SignaturePad from '@/components/theme/SignaturePad';

type Tab = 'student' | 'admin';
/** idle 正常；checking 电梯在查住户名单并下行；arriving 电梯到达，门要开了 */
type Phase = 'idle' | 'checking' | 'arriving';

const CHECK_MS = 1200;         // 查名单 + 电梯下行
const ARRIVE_MS = 1150;        // 到站、开门、跳转

/**
 * 楼层屏滚动的关键帧。行高随屏幕变，所以位移一律用百分比：
 * 一行占 roll 总高的 100/total，第一行本来就居中，往下停一行就多走一格。
 */
const rollKeyframes = (key: string, total: number, index: number | null) => {
  if (index == null || total < 2) return `@keyframes ${key} { 0%, 100% { transform: translateY(0); } }`;
  const cell = 100 / total;
  // -50% 对齐的是整块名单的中心，所以还要按行索引补上相对中心的偏移
  const at = (i: number) => `calc(-50% + ${((i - (total - 1) / 2) * cell).toFixed(3)}%)`;
  return `@keyframes ${key} { 0% { transform: translateY(-50%); } 62% { transform: translateY(${at(index - 0.42)}); animation-timing-function: cubic-bezier(.16,1,.3,1); } 100% { transform: translateY(${at(index)}); } }`;
};

/**
 * 登录页：门厅电梯。走廊用纯 CSS 搭，不依赖照片，因此没有贴图对位的麻烦。
 * 电梯门就是表单本身——楼层屏显示住户名单滚动到的楼层，门上方是当天日程。
 * 确认进入后电梯下行、到站、双扇门滑开，走进 4A。
 */
export default function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const setCurrent = useStudentStore((s) => s.setCurrent);
  const [tab, setTab] = useState<Tab>(params.get('admin') ? 'admin' : 'student');
  const [name, setName] = useState('');
  const [gender, setGender] = useState<Gender>('male');
  const [password, setPassword] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  // 新住户先在门厅登记表上签室友协议，再建档
  const [signing, setSigning] = useState(false);
  // 名单里没有的名字：滚动目标要在电梯启动前就定好，所以跟"显示协议"分开
  const [isNew, setIsNew] = useState(false);
  const [signature, setSignature] = useState('');
  const [roster, setRoster] = useState<string[]>([]);
  // 每次提交自增，动画只在自增时启动（pending 翻回 false 不会中断它）
  const [launch, setLaunch] = useState(0);
  const timers = useRef<number[]>([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);
  const wait = (ms: number) => new Promise((r) => { timers.current.push(window.setTimeout(r, ms)); });

  // 住户名单：名单越靠前的住户楼层越高，电梯下行层数就越多
  const enter = useMutation({
    mutationFn: async (): Promise<StudentResponse | null> => {
      const students = await listStudents({ limit: 500 });
      setRoster(students.map((s) => s.name));
      return students.find((s) => s.name === name.trim()) ?? null;
    },
    onSuccess: async (found) => {
      setIsNew(!found);
      setLaunch((n) => n + 1);
      await wait(CHECK_MS + ARRIVE_MS);
      if (!found) {
        setSigning(true);
        setPhase('idle');
        return;
      }
      setCurrent(found);
      navigate('/teaching', { replace: true });
    },
    onError: (e: Error) => { toast.error(e.message); resetLobby(); },
  });

  const register = useMutation({
    mutationFn: () => createStudent({ name: name.trim(), gender, signature }),
    onSuccess: async (s) => { setSigning(false); setLaunch((n) => n + 1); await wait(CHECK_MS + ARRIVE_MS); setCurrent(s); navigate('/teaching', { replace: true }); },
    onError: (e: Error) => { toast.error(e.message); resetLobby(); },
  });

  const admin = useMutation({
    mutationFn: () => adminLogin(password),
    onSuccess: async () => { setLaunch((n) => n + 1); await wait(CHECK_MS + ARRIVE_MS); navigate('/admin/knowledge', { replace: true }); },
    onError: (e: Error) => { toast.error(e.message); resetLobby(); },
  });

  const today = todayTheme();
  const base = import.meta.env.BASE_URL;
  const busy = enter.isPending || register.isPending || phase !== 'idle';
  const canEnter = name.trim().length > 0 && !busy;
  const who = name.trim() || '…';

  // 名单越靠前的住户住得越高，电梯要下行更多层才接到人；签协议时停在「新住户」
  const lines = isNew || signing ? [...roster, '新住户'] : roster;
  const found = lines.findIndex((r) => r === name.trim());
  const rollIndex = isNew || signing ? lines.length - 1 : found < 0 ? null : found;
  const rollKey = `roll-${lines.length}-${rollIndex ?? 'idle'}`;
  const onStudentSubmit = () => {
    setRoster([]);
    enter.mutate();
  };

  // 回退到登记台：楼层屏也跟着退回大厅
  const resetLobby = () => { setPhase('idle'); setLaunch(0); setIsNew(false); };

  // 一提交就把登记台收起来、电梯开始下行；到站后再开门
  useEffect(() => {
    if (!launch) return;
    setPhase('checking');
    const t = window.setTimeout(() => setPhase('arriving'), CHECK_MS);
    return () => clearTimeout(t);
  }, [launch]);

  return (
    <div className="agent">
      <style>{`
        .cab-roster .roll.go { animation-name: ${rollKey}; animation-duration: ${CHECK_MS}ms; }
        ${rollKeyframes(rollKey, lines.length, rollIndex)}
      `}</style>
      <div className={`login lobby phase-${phase}`}>
        <div className="hall" aria-hidden="true">
          <div className="hall-walls" />
          <div className="hall-carpet" />
          <div className="hall-light l" /><div className="hall-light r" />
        </div>

        <button type="button" className="lobby-brand" onClick={() => navigate('/')} title="回到首页">
          <BrandMark size={34} />
          <span className="wordmark"><span className="w1">STEM</span><span className="w2">Agent</span></span>
        </button>

        <div className="cab">
          <div className="cab-faceplate">
            <span className="floor-no">4A</span>
            <span className="floor-name">Learning Lab</span>
          </div>

          <div className="cab-roster" aria-hidden="true">
            <span className="roster-cap">Residents</span>
            <div className={`roll ${launch ? 'go' : ''}`}>
              <span className="floor-tag">大厅</span>
              {lines.map((nm) => <span key={nm} className="floor-tag">{nm}</span>)}
            </div>
          </div>

          <div className="cab-doors">
            <div className="panel l" /><div className="panel r" />
            <div className="seam" />
          </div>
        </div>
        <div className="cab-spill" aria-hidden="true" />

        <h1 className="lobby-say" aria-live="polite">
          {phase === 'arriving'
            ? (isNew ? `${who}，登记一下。` : `欢迎回来，${who}。`)
            : name.trim() ? `你好，${who}。` : LOGIN.headline}
        </h1>

        <section className="board">
          <div className="board-cap">
            <span className="kicker">{LOGIN.title}</span>
            <span className="today"><WeekdayIcon day={today.key} /><span>{today.en}</span></span>
          </div>

          <div className="tabs">
            <button type="button" className={tab === 'student' ? 'on' : ''} disabled={busy} onClick={() => setTab('student')}>学生</button>
            <button type="button" className={tab === 'admin' ? 'on' : ''} disabled={busy || signing} onClick={() => setTab('admin')}>教师</button>
          </div>

          {tab === 'student' && signing ? (
            <div className="agree">
              <h2 className="board-title">签署室友协议</h2>
              <p className="sub">{who}，第一次来 4A？进门前按 Sheldon 的规矩，先签一份室友协议。</p>
              <ol className="agree-terms">
                <li>讲解方式、讲师、提醒都写在协议里，随时可以改。</li>
                <li>摄像头只用来判断学习状态，画面不上传、不保存。</li>
                <li>不会的题尽管问，问题没有笨的。</li>
              </ol>
              <SignaturePad value={signature} onChange={setSignature} disabled={register.isPending} />
              <button type="button" className="cta" disabled={signature.length < 3 || busy} onClick={() => register.mutate()}>
                {register.isPending ? '登记中…' : '签字并取钥匙'}
              </button>
              <button type="button" className="back" disabled={busy} onClick={() => { setSigning(false); setSignature(''); resetLobby(); }}>‹ 改名字</button>
            </div>
          ) : tab === 'student' ? (
            <>
              <h2 className="board-title">{name.trim() ? '带你去 4A。' : `欢迎来到 4A。`}</h2>
              <p className="sub">报上名字，电梯会来接你。第一次来会先请你签一份室友协议。</p>
              <label className="fld">
                <span>你的名字</span>
                <input
                  type="text" value={name} placeholder="报上名来" maxLength={100} autoFocus disabled={busy}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && canEnter && onStudentSubmit()}
                />
              </label>
              <div className="fld">
                <span>第一次来的话</span>
                <div className="seg3">
                  {GENDER_OPTIONS.map((g) => (
                    <button type="button" key={g.value} className={gender === g.value ? 'on' : ''} disabled={busy} onClick={() => setGender(g.value)}>{g.label}</button>
                  ))}
                </div>
              </div>
              <button type="button" className="cta" disabled={!canEnter} onClick={onStudentSubmit}>
                {phase === 'idle' ? (enter.isPending ? '核对住户名单…' : '叫电梯') : phase === 'checking' ? '电梯下行…' : '门开了，走进去'}
              </button>
            </>
          ) : (
            <>
              <h2 className="board-title">管理台</h2>
              <p className="sub">{LOGIN.teacherSub}</p>
              <label className="fld">
                <span>口令</span>
                <input
                  type="password" value={password} placeholder={LOGIN.passwordPlaceholder} autoFocus
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && password && admin.mutate()}
                />
              </label>
              <button type="button" className="cta" disabled={!password || admin.isPending} onClick={() => admin.mutate()}>签署并进入</button>
              <div className="hint">口令由后端环境变量 ADMIN_PASSWORD 设置。</div>
            </>
          )}

          {!signing && <div className="ooo">{LOGIN.outOfOrder}</div>}
        </section>

        <p className="lobby-foot">Apartment 4A · 走廊尽头，右手边</p>
      </div>
      <Toasts />
    </div>
  );
}
