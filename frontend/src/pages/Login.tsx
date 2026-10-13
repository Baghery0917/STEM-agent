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
type Phase = 'idle' | 'knocking' | 'opening';

/** 走廊照片的原始尺寸与电梯木门在图中的位置（像素） */
const SCENE = { w: 1456, h: 914 };
const DOOR = { x: 626, y: 139, w: 274, h: 506 };

const KNOCK_GAP = 720;      // 每下敲门的间隔
const OPEN_AT = 3 * KNOCK_GAP + 300;
const ENTER_AT = OPEN_AT + 1100;

/**
 * 登录页：卡片就是电梯门。走廊照片按 cover 铺满，卡片用图中坐标贴在木门上，
 * 字像写在门上。输入名字后敲三下门（门板震动、涟漪、喊名字），门打开进入。
 * 名字没登记过的，先在门上签室友协议，签名随建档一起存下。
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
  // 新住户先在门上签室友协议，再建档敲门
  const [signing, setSigning] = useState(false);
  const [signature, setSignature] = useState('');
  const [knocks, setKnocks] = useState(0);
  const [scale, setScale] = useState(1);
  const timers = useRef<number[]>([]);

  // 场景缩放：等价于 background-size: cover
  useEffect(() => {
    const calc = () => setScale(Math.max(window.innerWidth / SCENE.w, window.innerHeight / SCENE.h));
    calc();
    window.addEventListener('resize', calc);
    return () => window.removeEventListener('resize', calc);
  }, []);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const knockAndOpen = (s: StudentResponse) => {
    setPhase('knocking');
    setKnocks(0);
    timers.current = [1, 2, 3].map((n) => window.setTimeout(() => setKnocks(n), n * KNOCK_GAP));
    timers.current.push(window.setTimeout(() => setPhase('opening'), OPEN_AT));
    timers.current.push(window.setTimeout(() => { setCurrent(s); navigate('/teaching', { replace: true }); }, ENTER_AT));
  };

  const enter = useMutation({
    mutationFn: async (): Promise<StudentResponse | null> => {
      const nm = name.trim();
      return (await listStudents({ limit: 500 })).find((s) => s.name === nm) ?? null;
    },
    onSuccess: (found) => (found ? knockAndOpen(found) : setSigning(true)),
    onError: (e: Error) => toast.error(e.message),
  });

  const register = useMutation({
    mutationFn: () => createStudent({ name: name.trim(), gender, signature }),
    onSuccess: (s) => { setSigning(false); knockAndOpen(s); },
    onError: (e: Error) => toast.error(e.message),
  });

  const admin = useMutation({
    mutationFn: () => adminLogin(password),
    onSuccess: () => navigate('/admin/knowledge', { replace: true }),
    onError: (e: Error) => toast.error(e.message),
  });

  const base = import.meta.env.BASE_URL;
  const today = todayTheme();
  const busy = enter.isPending || register.isPending || phase !== 'idle';
  const canEnter = name.trim().length > 0 && !busy;
  const who = name.trim() || '…';

  const sceneStyle = {
    width: SCENE.w * scale, height: SCENE.h * scale,
    left: (window.innerWidth - SCENE.w * scale) / 2, top: (window.innerHeight - SCENE.h * scale) / 2,
    ['--s' as string]: scale,
  };
  const doorStyle = { left: DOOR.x * scale, top: DOOR.y * scale, width: DOOR.w * scale, height: DOOR.h * scale };

  return (
    <div className="agent">
      <div className={`login scene-wrap phase-${phase}`}>
        <div className="scene" style={sceneStyle}>
          <img className="bg" src={`${base}tbbt/apartment/hallway-set-photo.jpg`} alt="" draggable={false} />
          <div className="veil" />
          <button type="button" className="topline" onClick={() => navigate('/')} title="回到首页">
            <BrandMark size={34} />
            <span className="wordmark"><span className="w1">STEM</span><span className="w2">Agent</span></span>
          </button>

          <div className={`door ${knocks ? `k${knocks}` : ''}`} style={doorStyle}>
            {/* 两扇门板：开门时左右滑开 */}
            <div className="leaf l" /><div className="leaf r" />
            <div className="glow" />
            {/* 敲门涟漪 */}
            {[1, 2, 3].map((n) => <span key={n} className={`ripple ${knocks >= n ? 'go' : ''}`} />)}

            <div className="face">
              <div className="kicker">{LOGIN.title}</div>
              <div className="today"><WeekdayIcon day={today.key} /><span>{today.en}</span></div>
              <h1>{tab === 'student' ? (signing ? '签署室友协议' : LOGIN.headline) : LOGIN.teacherTab}</h1>
              <div className="tabs">
                <button type="button" className={tab === 'student' ? 'on' : ''} disabled={busy} onClick={() => setTab('student')}>学生</button>
                <button type="button" className={tab === 'admin' ? 'on' : ''} disabled={busy || signing} onClick={() => setTab('admin')}>教师</button>
              </div>

              <div className="body">
                {tab === 'student' && signing ? (
                  <div className="agree">
                    <p className="sub">{name.trim()}，第一次来 4A？进门前按 Sheldon 的规矩，先签一份室友协议。</p>
                    <ol className="agree-terms">
                      <li>讲解方式、讲师、提醒都写在协议里，随时可以改。</li>
                      <li>摄像头只用来判断学习状态，画面不上传、不保存。</li>
                      <li>不会的题尽管问，问题没有笨的。</li>
                    </ol>
                    <SignaturePad value={signature} onChange={setSignature} disabled={register.isPending} />
                    <button type="button" className="enter" disabled={signature.length < 3 || busy} onClick={() => register.mutate()}>
                      {register.isPending ? '登记中…' : '签字并敲门'}
                    </button>
                    <button type="button" className="agree-back" disabled={busy} onClick={() => { setSigning(false); setSignature(''); }}>‹ 改名字</button>
                  </div>
                ) : tab === 'student' ? (
                  <>
                    <label className="fld">
                      <span>你的名字</span>
                      <input
                        type="text" value={name} placeholder="报上名来" maxLength={100} autoFocus disabled={busy}
                        onChange={(e) => setName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && canEnter && enter.mutate()}
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
                    <button type="button" className="enter" disabled={!canEnter} onClick={() => enter.mutate()}>
                      {phase === 'idle' ? (enter.isPending ? '查看信箱…' : '敲门') : phase === 'knocking' ? '敲门中…' : '门开了'}
                    </button>
                  </>
                ) : (
                  <>
                    <p className="sub">{LOGIN.teacherSub}</p>
                    <label className="fld">
                      <span>口令</span>
                      <input
                        type="password" value={password} placeholder={LOGIN.passwordPlaceholder} autoFocus
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && password && admin.mutate()}
                      />
                    </label>
                    <button type="button" className="enter" disabled={!password || admin.isPending} onClick={() => admin.mutate()}>签署并进入</button>
                    <div className="hint">口令由后端环境变量 ADMIN_PASSWORD 设置。</div>
                  </>
                )}
              </div>
              {!signing && <div className="ooo">{LOGIN.outOfOrder}</div>}
            </div>
          </div>

          {/* 敲门时在门上方喊名字，一声比一声大 */}
          <div className="call" style={{ left: (DOOR.x + DOOR.w / 2) * scale, top: (DOOR.y - 14) * scale }} aria-live="polite">
            {[1, 2, 3].map((n) => (
              <span key={n} className={`c${n} ${knocks >= n ? 'on' : ''}`}>{who}?</span>
            ))}
          </div>
        </div>
      </div>
      <Toasts />
    </div>
  );
}
