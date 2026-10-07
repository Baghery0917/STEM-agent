import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  cancelTeachingSession,
  endTeachingSession,
  getTeachingSession,
  rateMessage,
  startTeachingSession,
  streamChat,
} from '@/api/teaching';
import type { TeachingMessageResponse, TeachingSessionDetailResponse } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import { useCameraFrame } from '@/hooks/useCameraFrame';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import { getStudentReport } from '@/api/reports';
import TopBar from '@/components/shell/TopBar';
import Composer from '@/components/shell/Composer';
import EmotionBadge from '@/components/shell/EmotionBadge';
import Modal from '@/components/shell/Modal';
import AgentTrace from '@/components/teaching/AgentTrace';
import Message from '@/components/teaching/Message';
import SelfRate from '@/components/teaching/SelfRate';
import HandoffCard from '@/components/teaching/HandoffCard';
import { WEEKDAY_LINES } from '@/theme/copy';

interface HandoffState {
  practiceSessionId: number;
  questionIds: number[];
  label: string;
}

export default function Teaching() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const student = useStudentStore((s) => s.current)!;
  const camera = useCameraFrame();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [streamingText, setStreamingText] = useState('');
  const [sending, setSending] = useState(false);
  const [endOpen, setEndOpen] = useState(false);
  const [handoff, setHandoff] = useState<HandoffState | null>(
    (location.state as { handoff?: HandoffState } | null)?.handoff ?? null,
  );

  const sid = sessionId ? Number(sessionId) : undefined;

  const sessionQuery = useQuery({
    queryKey: ['teaching-session', sid],
    queryFn: () => getTeachingSession(sid!),
    enabled: !!sid,
    refetchInterval: (q) => {
      const s = q.state.data?.pipeline_status;
      return s === 'done' || s === 'failed' ? false : 800;
    },
  });

  const invalidateLists = () =>
    queryClient.invalidateQueries({ queryKey: ['teaching-sessions', student.id] });

  const startMutation = useMutation({
    mutationFn: startTeachingSession,
    onSuccess: (data) => {
      queryClient.setQueryData(['teaching-session', data.id], data);
      invalidateLists();
      setHandoff(null);
      navigate(`/teaching/${data.id}`, { replace: true });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const rateMutation = useMutation({
    mutationFn: rateMessage,
    onSuccess: (msg) => {
      queryClient.setQueryData<TeachingSessionDetailResponse>(['teaching-session', sid], (old) =>
        old ? { ...old, messages: old.messages.map((m) => (m.id === msg.id ? { ...m, self_rating: msg.self_rating } : m)) } : old,
      );
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const endMutation = useMutation({
    mutationFn: endTeachingSession,
    onSuccess: () => { toast.info('会话已结束'); setEndOpen(false); sessionQuery.refetch(); invalidateLists(); },
    onError: (err: Error) => toast.error(err.message),
  });

  const cancelMutation = useMutation({
    mutationFn: cancelTeachingSession,
    onSuccess: () => { toast.info('会话已取消'); invalidateLists(); navigate('/teaching'); },
    onError: (err: Error) => toast.error(err.message),
  });

  const session = sessionQuery.data;
  const messages = useMemo(
    () => [...(session?.messages ?? [])].sort((a, b) => a.sequence - b.sequence),
    [session?.messages],
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streamingText]);

  const latestEmotion = useMemo(() => {
    const u = [...messages].reverse().find((m) => m.role === 'user' && m.emotion_value != null);
    return u?.emotion_value ?? null;
  }, [messages]);

  const handleSend = async (text: string, image?: string | null) => {
    if (!sid || !session) {
      startMutation.mutate({
        student_id: student.id,
        question_content: text || '请帮我讲讲这道题',
        question_image: image ?? null,
        frame_base64: camera.captureFrame(),
        source_practice_session_id: handoff?.practiceSessionId ?? null,
        source_question_ids: handoff?.questionIds ?? null,
      });
      return;
    }
    if (sending) return;
    const maxSeq = messages.reduce((m, x) => Math.max(m, x.sequence), -1);
    const optimistic: TeachingMessageResponse = {
      id: -Date.now(), session_id: sid, role: 'user', content: text, message_type: 'chat',
      sequence: maxSeq + 1, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    };
    queryClient.setQueryData<TeachingSessionDetailResponse>(['teaching-session', sid], (old) =>
      old ? { ...old, messages: [...old.messages, optimistic] } : old,
    );
    setSending(true);
    setStreamingText('');
    await streamChat(
      { session_id: sid, message: text, frame_base64: camera.captureFrame() },
      {
        onDelta: (d) => setStreamingText((t) => t + d),
        onDone: async () => { setSending(false); setStreamingText(''); await sessionQuery.refetch(); invalidateLists(); },
        onError: async (err) => { setSending(false); setStreamingText(''); toast.error(err); await sessionQuery.refetch(); },
      },
    );
  };

  const emotionBadge = (
    <EmotionBadge
      videoRef={camera.videoRef}
      enabled={camera.enabled}
      status={camera.status}
      onToggle={camera.setEnabled}
      latestValue={latestEmotion}
    />
  );

  // ---------- 空状态：新对话 ----------
  if (!sid) {
    return (
      <>
        <TopBar crumb={handoff ? <><b>{handoff.label}</b> · 新会话</> : '新对话'} right={emotionBadge} />
        <section className="stage">
          <EmptyHero studentId={student.id} studentName={student.name} />
        </section>
        <Composer
          autoFocus
          loading={startMutation.isPending}
          placeholder={handoff ? '想问这道题的什么？直接写…' : undefined}
          modeHint="教学模式 · 一题一会话，可持续追问"
          context={handoff && (
            <span className="tg">
              {handoff.label} <span className="x" onClick={() => setHandoff(null)}>×</span>
            </span>
          )}
          onSend={handleSend}
        />
      </>
    );
  }

  if (!session) {
    return (
      <>
        <TopBar crumb="加载中…" right={emotionBadge} />
        <section className="stage"><div className="col muted">正在载入会话…</div></section>
      </>
    );
  }

  // ---------- 会话 ----------
  const isActive = session.status === 'active';
  const pipelineDone = session.pipeline_status === 'done' || session.pipeline_status === 'failed';
  const title = session.source_practice_session_id
    ? `来自练习 #${session.source_practice_session_id}`
    : (messages.find((m) => m.message_type === 'question_submit')?.content.split('\n')[0].slice(0, 28) ?? `会话 #${session.id}`);
  const turns = messages.filter((m) => m.role === 'user').length;
  const lastAssistantId = [...messages].reverse().find((m) => m.role === 'assistant')?.id;

  // 把消息按「用户 → (系统若干) → 助手」分组渲染
  const groups = groupMessages(messages);

  return (
    <>
      <TopBar
        crumb={<><b>{title}</b> · 第 {turns} 轮 · {isActive ? '进行中' : session.status === 'completed' ? '已结束' : '已取消'}</>}
        right={
          <>
            {isActive && (
              <>
                <button type="button" className="btn ghost sm" onClick={() => setEndOpen(true)}>结束会话</button>
                <button type="button" className="btn ghost sm danger" onClick={() => { if (confirm('取消后该会话不保存摘要，确定？')) cancelMutation.mutate(session.id); }}>取消</button>
              </>
            )}
            {emotionBadge}
          </>
        }
      />
      <section className="stage">
        <div className="col">
          {groups.map((g, gi) => (
            <div key={g.user.id}>
              <Message
                role="user"
                who={student.name.slice(0, 1)}
                content={g.user.message_type === 'question_submit' && session.source_practice_session_id ? undefined : g.user.content}
                before={g.user.message_type === 'question_submit' && session.source_practice_session_id
                  ? <HandoffCard practiceSessionId={session.source_practice_session_id} content={g.user.content} />
                  : undefined}
              />
              <Message
                role="ai"
                who="S"
                content={g.assistant?.content ?? (gi === groups.length - 1 && sending ? streamingText : undefined)}
                streaming={!g.assistant && gi === groups.length - 1 && sending}
                before={
                  (g.system.length > 0 || (gi === 0 && !pipelineDone)) ? (
                    <AgentTrace
                      pipelineStatus={gi === 0 ? session.pipeline_status : 'done'}
                      messages={g.system}
                      firstRound={gi === 0}
                      startedAt={g.user.created_at}
                      finishedAt={g.assistant?.created_at}
                    />
                  ) : undefined
                }
                after={g.assistant && (
                  <>
                    <div className="ai-actions">
                      <button type="button" onClick={() => { navigator.clipboard?.writeText(g.assistant!.content); toast.info('已复制'); }}>复制</button>
                      {isActive && pipelineDone && (
                        <>
                          <button type="button" onClick={() => handleSend('请换一种方式再讲一遍')}>重新讲</button>
                          <button type="button" onClick={() => handleSend('讲得太快了，能不能拆得再细一点')}>讲得太快</button>
                          <button type="button" onClick={() => handleSend('这部分我懂了，可以讲快一点')}>讲得太慢</button>
                        </>
                      )}
                    </div>
                    {g.assistant.id === lastAssistantId && (
                      <SelfRate
                        value={g.assistant.self_rating}
                        disabled={!isActive || rateMutation.isPending}
                        onChange={(v) => rateMutation.mutate({ session_id: session.id, message_id: g.assistant!.id, rating: v })}
                      />
                    )}
                  </>
                )}
              />
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </section>
      <Composer
        disabled={!isActive || !pipelineDone}
        loading={sending}
        placeholder={!pipelineDone ? '讲解生成中，稍候即可追问…' : isActive ? '接着问这道题…' : '会话已结束'}
        modeHint="教学模式 · 可持续追问"
        allowImage={false}
        onSend={handleSend}
      />
      <Modal
        open={endOpen}
        title="结束教学会话"
        onClose={() => setEndOpen(false)}
        footer={
          <>
            <button type="button" className="btn" onClick={() => setEndOpen(false)}>再想想</button>
            <button type="button" className="btn pri" disabled={endMutation.isPending} onClick={() => endMutation.mutate({ session_id: session.id })}>确认结束</button>
          </>
        }
      >
        <p>结束后会把这次的掌握度自评和情绪记录归档到你的学习画像。没有自评也可以结束，掌握度保持不变。</p>
      </Modal>
    </>
  );
}

interface Group {
  user: TeachingMessageResponse;
  system: TeachingMessageResponse[];
  assistant?: TeachingMessageResponse;
}

function groupMessages(messages: TeachingMessageResponse[]): Group[] {
  const groups: Group[] = [];
  let cur: Group | null = null;
  for (const m of messages) {
    if (m.role === 'user') {
      cur = { user: m, system: [] };
      groups.push(cur);
    } else if (!cur) {
      continue;
    } else if (m.role === 'system') {
      cur.system.push(m);
    } else if (m.role === 'assistant') {
      if (cur.assistant) {
        // 连续两条助手消息（兜底回复后的流式回复），拆成新组挂在同一用户消息下
        cur = { user: cur.user, system: [], assistant: m };
        groups.push(cur);
      } else {
        cur.assistant = m;
      }
    }
  }
  return groups;
}

function EmptyHero({ studentId, studentName }: { studentId: number; studentName: string }) {
  const navigate = useNavigate();
  const tree = useKnowledgeTree();
  const report = useQuery({
    queryKey: ['student-report', studentId, 'recent', 'nosummary'],
    queryFn: () => getStudentReport(studentId, 'recent', false),
    staleTime: 60_000,
  });
  const hour = new Date().getHours();
  const greet = hour < 6 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好';
  const weekdayLine = WEEKDAY_LINES[new Date().getDay()];
  const weak = [...(report.data?.knowledge_points ?? [])]
    .filter((k) => k.total_practice_count > 0)
    .sort((a, b) => a.mastery_level - b.mastery_level)[0];
  const sectionCount = tree.data?.sections.length ?? 0;

  return (
    <div className="hero">
      <h1 className="hi">
        {greet}，{studentName}。<br />把题目发给我，<em>我们一起把它讲透。</em>
      </h1>
      <div className="weekday">{weekdayLine}</div>
      <p>文字、拍照、截图都可以。我会先看你在这个知识点上的历史，再决定怎么讲。</p>
      <div className="chips">
        {weak && (
          <button type="button" className="chip" onClick={() => navigate('/practice/new', { state: { preselect: [weak.section_id] } })}>
            <span className="k warn">薄弱</span>{weak.section_title} 掌握度 {Math.round(weak.mastery_level * 100)}%，来几道练练
          </button>
        )}
        <button type="button" className="chip" onClick={() => navigate('/practice/new')}>
          <span className="k">练</span>开始一组练习{sectionCount ? ` · ${sectionCount} 个知识点可选` : ''}
        </button>
        <button type="button" className="chip" onClick={() => navigate('/report')}>
          <span className="k">看</span>看看最近的学习报告
        </button>
      </div>
    </div>
  );
}
