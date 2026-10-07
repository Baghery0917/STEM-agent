import { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createStudent, listStudents } from '@/api/students';
import { adminLogin } from '@/api/admin';
import type { Gender, StudentResponse } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import Toasts from '@/components/shell/Toasts';
import { GENDER_LABEL, GENDER_OPTIONS } from '@/utils/enums';
import { KNOCK_NAME_FALLBACK, LOGIN } from '@/theme/copy';
import { IconAtom } from '@/components/theme/Icons';

type Tab = 'student' | 'admin';

/** 登录页：公寓走廊。电梯贴着警戒带，门口信箱上的名牌就是学生名单。 */
export default function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const setCurrent = useStudentStore((s) => s.setCurrent);
  const [tab, setTab] = useState<Tab>(params.get('admin') ? 'admin' : 'student');
  const [name, setName] = useState('');
  const [gender, setGender] = useState<Gender>('male');
  const [password, setPassword] = useState('');
  const [hover, setHover] = useState<string | null>(null);
  const [knocks, setKnocks] = useState(0);

  const students = useQuery({
    queryKey: ['students', 'login'],
    queryFn: () => listStudents({ limit: 100 }),
    enabled: tab === 'student',
  });
  const create = useMutation({
    mutationFn: () => createStudent({ name: name.trim(), gender }),
    onSuccess: (s) => { toast.info(`已创建 ${s.name}`); pick(s); },
    onError: (e: Error) => toast.error(e.message),
  });
  const admin = useMutation({
    mutationFn: () => adminLogin(password),
    onSuccess: () => navigate('/admin/knowledge', { replace: true }),
    onError: (e: Error) => toast.error(e.message),
  });

  // 敲门三次，每次喊一声名字：悬停到谁的名牌就喊谁
  useEffect(() => {
    setKnocks(0);
    if (!hover) return;
    const timers = [1, 2, 3].map((n) => setTimeout(() => setKnocks(n), n * 420));
    return () => timers.forEach(clearTimeout);
  }, [hover]);

  const pick = (s: StudentResponse) => { setCurrent(s); navigate('/teaching', { replace: true }); };
  const base = import.meta.env.BASE_URL;
  const callName = hover ?? KNOCK_NAME_FALLBACK;

  return (
    <div className="agent">
      <div className="login hallway" style={{ backgroundImage: `url(${base}tbbt/apartment/hallway-set-photo.jpg)` }}>
        <div className="veil" />
        <div className="knock" aria-live="polite">
          {[1, 2, 3].map((n) => (
            <span key={n} className={knocks >= n ? 'on' : ''}>{callName}?</span>
          ))}
        </div>
        <div className="card door"><div className="bd">
          <div className="plate"><IconAtom width={18} height={18} /><span>{LOGIN.title}</span></div>
          <h1>STEM Agent</h1>
          <div className="radio" style={{ marginBottom: 14 }}>
            <button type="button" className={tab === 'student' ? 'on' : ''} onClick={() => setTab('student')}>学生</button>
            <button type="button" className={tab === 'admin' ? 'on' : ''} onClick={() => setTab('admin')}>教师 / 管理员</button>
          </div>

          {tab === 'student' ? (
            <>
              <div className="sub">{LOGIN.subtitle}</div>
              {students.isLoading && <div className="empty-note">加载中…</div>}
              <div className="mailbox">
                {students.data?.map((s) => (
                  <button
                    type="button"
                    key={s.id}
                    className="pick"
                    onMouseEnter={() => setHover(s.name)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(s.name)}
                    onBlur={() => setHover(null)}
                    onClick={() => pick(s)}
                  >
                    <span className="avatar">{s.name.slice(0, 1)}</span>
                    <span><div className="nm">{s.name}</div><div className="d">学号 #{s.id} · {GENDER_LABEL[s.gender]}</div></span>
                  </button>
                ))}
              </div>
              {students.data?.length === 0 && <div className="empty-note">信箱还是空的，先登记一个名字</div>}
              <div className="field">
                <input
                  type="text"
                  value={name}
                  placeholder="新学生姓名"
                  maxLength={100}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && name.trim() && create.mutate()}
                />
                <div className="radio">
                  {GENDER_OPTIONS.map((g) => (
                    <button type="button" key={g.value} className={gender === g.value ? 'on' : ''} onClick={() => setGender(g.value)}>{g.label}</button>
                  ))}
                </div>
                <button type="button" className="btn pri" disabled={!name.trim() || create.isPending} onClick={() => create.mutate()}>登记并进门</button>
              </div>
            </>
          ) : (
            <>
              <div className="plate agreement">{LOGIN.teacherTab}</div>
              <div className="sub">{LOGIN.teacherSub}</div>
              <div className="field">
                <input
                  type="password"
                  value={password}
                  placeholder={LOGIN.passwordPlaceholder}
                  autoFocus
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && password && admin.mutate()}
                />
                <button type="button" className="btn pri" disabled={!password || admin.isPending} onClick={() => admin.mutate()}>签署并进入</button>
              </div>
              <div className="hint" style={{ marginTop: 10 }}>口令由后端环境变量 ADMIN_PASSWORD 设置。</div>
            </>
          )}
          <div className="ooo">{LOGIN.outOfOrder}</div>
        </div></div>
      </div>
      <Toasts />
    </div>
  );
}
