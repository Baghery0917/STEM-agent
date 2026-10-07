import { useRef, useState } from 'react';
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
import { IconAtom } from '@/components/theme/Icons';

type Tab = 'student' | 'admin';

const KNOCK_MS = 380;

/**
 * 登录页：公寓走廊。输入自己的名字敲门进入；名字已登记就直接进，没登记就新建。
 * 不展示其他学生的名单。
 */
export default function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const setCurrent = useStudentStore((s) => s.setCurrent);
  const [tab, setTab] = useState<Tab>(params.get('admin') ? 'admin' : 'student');
  const [name, setName] = useState('');
  const [gender, setGender] = useState<Gender>('male');
  const [password, setPassword] = useState('');
  const [knocks, setKnocks] = useState(0);
  const [knocking, setKnocking] = useState(false);
  const timers = useRef<number[]>([]);

  // 敲三下门，每下喊一声名字，然后进门
  const knock = () =>
    new Promise<void>((resolve) => {
      setKnocking(true);
      setKnocks(0);
      timers.current.forEach(clearTimeout);
      timers.current = [1, 2, 3].map((n) => window.setTimeout(() => setKnocks(n), n * KNOCK_MS));
      timers.current.push(window.setTimeout(resolve, 3 * KNOCK_MS + 500));
    });

  const enter = useMutation({
    mutationFn: async (): Promise<StudentResponse> => {
      const nm = name.trim();
      const found = (await listStudents({ limit: 500 })).find((s) => s.name === nm);
      return found ?? createStudent({ name: nm, gender });
    },
    onSuccess: async (s) => {
      await knock();
      setCurrent(s);
      navigate('/teaching', { replace: true });
    },
    onError: (e: Error) => { setKnocking(false); toast.error(e.message); },
  });

  const admin = useMutation({
    mutationFn: () => adminLogin(password),
    onSuccess: () => navigate('/admin/knowledge', { replace: true }),
    onError: (e: Error) => toast.error(e.message),
  });

  const base = import.meta.env.BASE_URL;
  const canEnter = name.trim().length > 0 && !enter.isPending && !knocking;

  return (
    <div className="agent">
      <div className="login hallway" style={{ backgroundImage: `url(${base}tbbt/apartment/hallway-set-photo.jpg)` }}>
        <div className="veil" />
        <div className="glass">
          <div className="knock" aria-live="polite">
            {[1, 2, 3].map((n) => (
              <span key={n} className={knocks >= n ? 'on' : ''}>{name.trim() || '…'}?</span>
            ))}
          </div>
          <div className="plate"><IconAtom width={16} height={16} /><span>{LOGIN.title}</span></div>
          <h1>STEM Agent</h1>
          <div className="tabs">
            <button type="button" className={tab === 'student' ? 'on' : ''} onClick={() => setTab('student')}>学生</button>
            <button type="button" className={tab === 'admin' ? 'on' : ''} onClick={() => setTab('admin')}>教师 / 管理员</button>
          </div>

          {tab === 'student' ? (
            <>
              <div className="sub">{LOGIN.subtitle}</div>
              <label className="fld">
                <span>你的名字</span>
                <input
                  type="text"
                  value={name}
                  placeholder="报上名来"
                  maxLength={100}
                  autoFocus
                  disabled={knocking}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && canEnter && enter.mutate()}
                />
              </label>
              <div className="fld">
                <span>第一次来的话</span>
                <div className="seg3">
                  {GENDER_OPTIONS.map((g) => (
                    <button type="button" key={g.value} className={gender === g.value ? 'on' : ''} onClick={() => setGender(g.value)}>{g.label}</button>
                  ))}
                </div>
              </div>
              <button type="button" className="enter" disabled={!canEnter} onClick={() => enter.mutate()}>
                {knocking ? '敲门中…' : '敲门进入'}
              </button>
            </>
          ) : (
            <>
              <div className="plate agreement">{LOGIN.teacherTab}</div>
              <div className="sub">{LOGIN.teacherSub}</div>
              <label className="fld">
                <span>口令</span>
                <input
                  type="password"
                  value={password}
                  placeholder={LOGIN.passwordPlaceholder}
                  autoFocus
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && password && admin.mutate()}
                />
              </label>
              <button type="button" className="enter" disabled={!password || admin.isPending} onClick={() => admin.mutate()}>签署并进入</button>
              <div className="hint">口令由后端环境变量 ADMIN_PASSWORD 设置。</div>
            </>
          )}
          <div className="ooo">{LOGIN.outOfOrder}</div>
        </div>
      </div>
      <Toasts />
    </div>
  );
}
