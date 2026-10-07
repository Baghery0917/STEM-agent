import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createStudent, listStudents } from '@/api/students';
import { adminLogin } from '@/api/admin';
import type { Gender, StudentResponse } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import Toasts from '@/components/shell/Toasts';
import { GENDER_LABEL, GENDER_OPTIONS } from '@/utils/enums';

type Tab = 'student' | 'admin';

export default function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const setCurrent = useStudentStore((s) => s.setCurrent);
  const [tab, setTab] = useState<Tab>(params.get('admin') ? 'admin' : 'student');
  const [name, setName] = useState('');
  const [gender, setGender] = useState<Gender>('male');
  const [password, setPassword] = useState('');

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

  const pick = (s: StudentResponse) => { setCurrent(s); navigate('/teaching', { replace: true }); };

  return (
    <div className="agent">
      <div className="login">
        <div className="card"><div className="bd">
          <h1>STEM Agent</h1>
          <div className="radio" style={{ marginBottom: 14 }}>
            <button type="button" className={tab === 'student' ? 'on' : ''} onClick={() => setTab('student')}>学生</button>
            <button type="button" className={tab === 'admin' ? 'on' : ''} onClick={() => setTab('admin')}>教师 / 管理员</button>
          </div>

          {tab === 'student' ? (
            <>
              <div className="sub">选择一个学生进入，或者新建一个</div>
              {students.isLoading && <div className="empty-note">加载中…</div>}
              {students.data?.map((s) => (
                <button type="button" key={s.id} className="pick" onClick={() => pick(s)}>
                  <span className="avatar">{s.name.slice(0, 1)}</span>
                  <span><div className="nm">{s.name}</div><div className="d">学号 #{s.id} · {GENDER_LABEL[s.gender]}</div></span>
                </button>
              ))}
              {students.data?.length === 0 && <div className="empty-note">还没有学生，先创建一个</div>}
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
                <button type="button" className="btn pri" disabled={!name.trim() || create.isPending} onClick={() => create.mutate()}>创建并进入</button>
              </div>
            </>
          ) : (
            <>
              <div className="sub">输入管理口令进入管理台（知识树、题库、学生、数据库）</div>
              <div className="field">
                <input
                  type="password"
                  value={password}
                  placeholder="管理口令"
                  autoFocus
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && password && admin.mutate()}
                />
                <button type="button" className="btn pri" disabled={!password || admin.isPending} onClick={() => admin.mutate()}>进入管理台</button>
              </div>
              <div className="hint" style={{ marginTop: 10 }}>口令由后端环境变量 ADMIN_PASSWORD 设置。</div>
            </>
          )}
        </div></div>
      </div>
      <Toasts />
    </div>
  );
}
