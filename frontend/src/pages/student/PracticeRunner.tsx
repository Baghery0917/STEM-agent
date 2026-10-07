import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  endPractice, getPracticeSession, skipQuestion, starQuestion, submitAnswer,
} from '@/api/practice';
import type {
  PracticeSessionDetailResponse, PracticeSessionResponse, QuestionPublicResponse, StartSessionResponse,
} from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import { useCameraFrame } from '@/hooks/useCameraFrame';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import TopBar from '@/components/shell/TopBar';
import EmotionBadge from '@/components/shell/EmotionBadge';
import QuestionCard, { type ItemState } from '@/components/practice/QuestionCard';
import ProgressBar from '@/components/practice/ProgressBar';
import PracticeSummary from '@/components/practice/PracticeSummary';
import AtomSpinner from '@/components/theme/AtomSpinner';

export default function PracticeRunner() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const sid = Number(sessionId);
  const location = useLocation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const student = useStudentStore((s) => s.current)!;
  const camera = useCameraFrame();
  const tree = useKnowledgeTree();

  const initial = location.state as StartSessionResponse | undefined;

  // 以服务端详情为准；刚开始时用 location.state 先渲染
  const detail = useQuery({
    queryKey: ['practice-session', sid],
    queryFn: () => getPracticeSession(sid),
    enabled: !!sid,
    initialData: initial && initial.session.id === sid
      ? ({ ...initial.session, questions: initial.questions, items: [] } as PracticeSessionDetailResponse)
      : undefined,
  });

  const session: PracticeSessionResponse | undefined = detail.data;
  const questions: QuestionPublicResponse[] = useMemo(() => detail.data?.questions ?? [], [detail.data?.questions]);

  // 本地状态：每题的作答/跳过结果、草稿、当前题
  const [states, setStates] = useState<Record<number, ItemState>>({});
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [index, setIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [showSummary, setShowSummary] = useState(false);
  const qStartRef = useRef<number>(Date.now());

  // 从服务端 items 恢复本地状态（刷新页面 / 从历史进入）
  useEffect(() => {
    const items = detail.data?.items ?? [];
    if (!items.length) return;
    setStates((prev) => {
      const next = { ...prev };
      for (const it of items) {
        if (next[it.question_id]) continue;
        const reveal = detail.data!.instant_feedback || !!detail.data!.ended_at;
        next[it.question_id] = it.is_skipped
          ? { kind: 'skipped' }
          : {
              kind: 'answered',
              answer: it.user_answer,
              feedback: {
                item: it,
                is_correct: reveal ? it.is_correct : null,
                correct_answer: reveal ? it.question?.answer ?? '' : null,
                analysis: reveal ? it.question?.analysis ?? null : null,
                analysis_image: reveal ? it.question?.analysis_image ?? null : null,
                session: detail.data!,
              },
            };
      }
      return next;
    });
  }, [detail.data]);

  // 首次进入：跳到第一道未做的题
  const firstPendingDone = useRef(false);
  useEffect(() => {
    if (firstPendingDone.current || !questions.length) return;
    const items = detail.data?.items ?? [];
    if (!items.length && !initial) return;
    const done = new Set(items.map((i) => i.question_id));
    const i = questions.findIndex((q) => !done.has(q.id));
    setIndex(i === -1 ? questions.length - 1 : i);
    firstPendingDone.current = true;
  }, [questions, detail.data, initial]);

  // 计时
  useEffect(() => {
    if (!session?.timed || session.ended_at) return;
    const startedAt = new Date(session.started_at).getTime();
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - startedAt) / 1000)), 1000);
    return () => clearInterval(t);
  }, [session?.timed, session?.started_at, session?.ended_at]);

  const current = questions[index];
  const curState: ItemState = current ? states[current.id] ?? { kind: 'pending' } : { kind: 'pending' };
  const starred = useMemo(() => new Set(session?.starred_question_ids ?? []), [session?.starred_question_ids]);

  useEffect(() => {
    qStartRef.current = Date.now();
  }, [current?.id]);

  const updateSession = useCallback((s: PracticeSessionResponse) => {
    qc.setQueryData<PracticeSessionDetailResponse>(['practice-session', sid], (old) => (old ? { ...old, ...s } : old));
    qc.invalidateQueries({ queryKey: ['practice-sessions', student.id] });
  }, [qc, sid, student.id]);

  const submit = useMutation({
    mutationFn: (q: QuestionPublicResponse) => submitAnswer(sid, {
      question_id: q.id,
      user_answer: (drafts[q.id] ?? '').trim(),
      duration_seconds: Math.round((Date.now() - qStartRef.current) / 1000),
      frame_base64: camera.captureFrame(),
    }),
    onSuccess: (fb, q) => {
      setStates((s) => ({ ...s, [q.id]: { kind: 'answered', answer: (drafts[q.id] ?? '').trim(), feedback: fb } }));
      updateSession(fb.session);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const end = useMutation({
    mutationFn: () => endPractice(sid),
    onSuccess: (s) => {
      updateSession(s);
      // 统一批改：结束后清掉本地遮罩状态，用服务端详情重建以显示答案
      if (!s.instant_feedback) setStates({});
      detail.refetch();
      setShowSummary(true);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const goPrev = () => setIndex((i) => Math.max(0, i - 1));
  const goNext = useCallback(() => {
    if (index + 1 >= questions.length) {
      const allDone = questions.every((q) => states[q.id] && states[q.id].kind !== 'pending');
      if (session && !session.ended_at && allDone) end.mutate();
      else if (session?.ended_at) setShowSummary(true);
      return;
    }
    setIndex((i) => i + 1);
  }, [index, questions, states, session, end]);

  const skip = useMutation({
    mutationFn: (q: QuestionPublicResponse) => skipQuestion(sid, {
      question_id: q.id,
      duration_seconds: Math.round((Date.now() - qStartRef.current) / 1000),
    }),
    onSuccess: (res, q) => {
      setStates((s) => ({ ...s, [q.id]: { kind: 'skipped' } }));
      updateSession(res.session);
      if (index + 1 < questions.length) setIndex((i) => i + 1);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const star = useMutation({
    mutationFn: (q: QuestionPublicResponse) => starQuestion(sid, { question_id: q.id, starred: !starred.has(q.id) }),
    onSuccess: updateSession,
    onError: (e: Error) => toast.error(e.message),
  });

  const busy = submit.isPending || skip.isPending;

  const askThis = (q: QuestionPublicResponse) => {
    const pos = questions.findIndex((x) => x.id === q.id) + 1;
    navigate('/teaching', {
      state: { handoff: { practiceSessionId: sid, questionIds: [q.id], label: `练习 #${sid} 第 ${pos} 题` } },
    });
  };

  // 键盘：A-H 选择、Enter 提交、←/→ 切题
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === 'TEXTAREA' || tag === 'INPUT';
      if (!current || showSummary) return;
      if (e.key === 'ArrowLeft' && !typing) { goPrev(); return; }
      if (e.key === 'ArrowRight' && !typing) { goNext(); return; }
      if (curState.kind !== 'pending') return;
      if (e.key === 'Enter' && !typing) {
        if ((drafts[current.id] ?? '').trim()) submit.mutate(current);
        return;
      }
      const k = e.key.toUpperCase();
      if (!typing && /^[A-H]$/.test(k) && (current.type === 'single_choice' || current.type === 'multiple_choice')) {
        setDrafts((d) => {
          if (current.type === 'single_choice') return { ...d, [current.id]: k };
          const set = new Set((d[current.id] ?? '').split('').filter(Boolean));
          if (set.has(k)) set.delete(k); else set.add(k);
          return { ...d, [current.id]: [...set].sort().join('') };
        });
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [current, curState.kind, drafts, goNext, showSummary, submit]);

  const emotionBadge = (
    <EmotionBadge videoRef={camera.videoRef} enabled={camera.enabled} status={camera.status} onToggle={camera.setEnabled} />
  );

  if (!session) {
    return (
      <>
        <TopBar crumb="加载中…" right={emotionBadge} />
        <section className="stage">
          <div className="pwrap muted">
            {detail.isError ? `加载失败：${(detail.error as Error).message}` : <><AtomSpinner size={18} /> 正在载入练习…</>}
          </div>
        </section>
      </>
    );
  }

  const scopeNames = session.knowledge_point_ids
    .map((id) => tree.data?.sectionById.get(id)?.title)
    .filter(Boolean) as string[];
  const scope = scopeNames.slice(0, 2).join('、') || '练习';
  const ended = !!session.ended_at;
  const confirmEnd = () => {
    if (confirm('未作答的题会按跳过处理，确定结束？')) end.mutate();
  };

  if (ended && (showSummary || !current)) {
    return (
      <>
        <TopBar crumb={<><b>{scope} · {session.total_count} 题</b> · 已完成</>} right={emotionBadge} />
        <section className="stage">
          <PracticeSummary
            session={session}
            questions={questions}
            items={detail.data?.items ?? []}
            scope={scope}
            onReview={(i) => { setShowSummary(false); setIndex(i); }}
            onAsk={(ids) => navigate('/teaching', {
              state: {
                handoff: {
                  practiceSessionId: sid,
                  questionIds: ids,
                  label: ids.length === 1
                    ? `练习 #${sid} 第 ${questions.findIndex((q) => q.id === ids[0]) + 1} 题`
                    : `练习 #${sid} · ${ids.length} 题`,
                },
              },
            })}
            onAgain={() => navigate('/practice/new', { state: { preselect: session.knowledge_point_ids } })}
          />
        </section>
      </>
    );
  }

  const stateList = questions.map((q) => states[q.id] ?? { kind: 'pending' as const });

  return (
    <>
      <TopBar
        crumb={<><b>{scope} · {session.total_count} 题</b> · {session.timed ? '计时' : '不计时'} · {ended ? '回顾' : '进行中'}</>}
        right={emotionBadge}
      />
      <section className="stage">
        <div className="pwrap">
          <ProgressBar
            timed={session.timed}
            index={index}
            total={questions.length}
            states={stateList}
            starred={starred}
            questionIds={questions.map((q) => q.id)}
            correct={session.correct_count}
            wrong={session.wrong_count}
            skipped={session.skip_count}
            elapsedSec={elapsed}
            revealed={session.instant_feedback || ended}
            onJump={setIndex}
            onEnd={() => (ended ? setShowSummary(true) : confirmEnd())}
          />
          {current && (
            <QuestionCard
              index={index}
              total={questions.length}
              question={current}
              sectionTitle={current.knowledge_point_ids.map((id) => tree.data?.sectionById.get(id)?.title).filter(Boolean)[0]}
              state={ended && curState.kind === 'pending' ? { kind: 'skipped' } : curState}
              draft={drafts[current.id] ?? ''}
              onDraft={(v) => setDrafts((d) => ({ ...d, [current.id]: v }))}
              starred={starred.has(current.id)}
              timed={session.timed && !ended}
              revealed={session.instant_feedback || ended}
              onStar={() => star.mutate(current)}
              onAsk={() => askThis(current)}
              onPrev={index > 0 ? goPrev : undefined}
              onNext={goNext}
              onSubmit={() => submit.mutate(current)}
              onSkip={() => skip.mutate(current)}
              busy={busy}
            />
          )}
          <div className="qfoot-note">
            {ended ? '练习已结束 · 这是回顾' : session.timed ? '计时中 · 做完统一批改，卡住就星标' : session.instant_feedback ? '不计时 · 每题即时反馈，随时可以转去提问' : '不计时 · 做完统一批改，随时可以转去提问'}
          </div>
        </div>
      </section>
      <div className="composer-wrap">
        <div className="composer wide">
          <div className="actbar">
            <span className="hintk">
              {ended
                ? '回顾模式 · 可以逐题问老师'
                : session.timed
                  ? '计时中 · 每题可跳过（0 分），卡住就星标'
                  : '不计时 · 每题可跳过（0 分），随时可转去提问'}
            </span>
            <span className="sp" />
            {ended
              ? <button type="button" className="btn ghost sm" onClick={() => setShowSummary(true)}>查看总结</button>
              : <button type="button" className="btn ghost sm" onClick={confirmEnd}>结束练习</button>}
          </div>
        </div>
      </div>
    </>
  );
}
