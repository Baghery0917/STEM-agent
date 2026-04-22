import { useEffect, useRef, useState, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import {
  App,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Slider,
  Space,
  Spin,
  Typography,
} from 'antd';
import { CloseCircleOutlined, StopOutlined } from '@ant-design/icons';
import {
  cancelTeachingSession,
  endTeachingSession,
  getTeachingSession,
  startTeachingSession,
  streamChat,
} from '@/api/teaching';
import type { TeachingMessageResponse, TeachingSessionDetailResponse } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import ChatBubble from '@/components/teaching/ChatBubble';
import ChatInput from '@/components/teaching/ChatInput';
import PipelineProgress from '@/components/teaching/PipelineProgress';
import StrategyPanel from '@/components/teaching/StrategyPanel';
import SessionHistorySidebar from '@/components/teaching/SessionHistorySidebar';

export default function Teaching() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { message, modal } = App.useApp();
  const student = useStudentStore((s) => s.current);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [endOpen, setEndOpen] = useState(false);
  const [mastery, setMastery] = useState(0);
  const [streamingText, setStreamingText] = useState('');
  const [sending, setSending] = useState(false);

  const sessionQuery = useQuery({
    queryKey: ['teaching-session', sessionId],
    queryFn: () => getTeachingSession(Number(sessionId)),
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const s = query.state.data?.pipeline_status;
      return s === 'done' || s === 'failed' ? false : 800;
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessionQuery.data?.messages.length]);

  const startMutation = useMutation({
    mutationFn: startTeachingSession,
    onSuccess: (data) => {
      queryClient.setQueryData(['teaching-session', String(data.id)], data);
      if (student) {
        queryClient.invalidateQueries({ queryKey: ['teaching-sessions', student.id] });
      }
      navigate(`/teaching/${data.id}`, { replace: true });
    },
    onError: (err: Error) => message.error(err.message),
  });

  const sessionKey = (id: number) => ['teaching-session', String(id)];

  const handleSend = async (msg: string) => {
    if (!sessionQuery.data || sending) return;
    const sid = sessionQuery.data.id;
    const maxSeq = sessionQuery.data.messages.reduce(
      (m, x) => Math.max(m, x.sequence),
      -1,
    );
    const optimisticUser: TeachingMessageResponse = {
      id: -Date.now(),
      session_id: sid,
      role: 'user',
      content: msg,
      message_type: 'chat',
      sequence: maxSeq + 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    queryClient.setQueryData<TeachingSessionDetailResponse>(sessionKey(sid), (old) =>
      old ? { ...old, messages: [...old.messages, optimisticUser] } : old,
    );
    setSending(true);
    setStreamingText('');
    await streamChat(
      { session_id: sid, message: msg },
      {
        onDelta: (delta) => setStreamingText((t) => t + delta),
        onDone: async () => {
          setSending(false);
          setStreamingText('');
          await sessionQuery.refetch();
        },
        onError: async (err) => {
          setSending(false);
          setStreamingText('');
          message.error(err);
          await sessionQuery.refetch();
        },
      },
    );
  };

  const endMutation = useMutation({
    mutationFn: endTeachingSession,
    onSuccess: () => {
      message.success('会话已结束');
      setEndOpen(false);
      sessionQuery.refetch();
      if (student) {
        queryClient.invalidateQueries({ queryKey: ['teaching-sessions', student.id] });
      }
    },
    onError: (err: Error) => message.error(err.message),
  });

  const cancelMutation = useMutation({
    mutationFn: cancelTeachingSession,
    onSuccess: () => {
      message.info('会话已取消');
      sessionQuery.refetch();
      if (student) {
        queryClient.invalidateQueries({ queryKey: ['teaching-sessions', student.id] });
      }
    },
    onError: (err: Error) => message.error(err.message),
  });

  if (!student) return null;

  const activeSessionId = sessionId ? Number(sessionId) : undefined;

  let centerContent: ReactNode;
  let rightContent: ReactNode = null;

  if (!sessionId) {
    centerContent = (
      <StartSessionView onSubmit={startMutation.mutate} loading={startMutation.isPending} />
    );
  } else if (sessionQuery.isLoading || !sessionQuery.data) {
    centerContent = (
      <div style={{ textAlign: 'center', padding: 64 }}>
        <Spin />
      </div>
    );
  } else {
    const session = sessionQuery.data;
    const isActive = session.status === 'active';
    const pipelineDone = session.pipeline_status === 'done';
    const visibleMessages = [...session.messages].sort((a, b) => a.sequence - b.sequence);

    centerContent = (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#f7f8fa' }}>
        <div
          style={{
            padding: '12px 20px',
            borderBottom: '1px solid #f0f0f0',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <Typography.Title level={5} style={{ margin: 0, flex: 1 }}>
            教学会话 #{session.id}
          </Typography.Title>
          {isActive && (
            <>
              <Button
                icon={<CloseCircleOutlined />}
                onClick={() => {
                  setMastery(0);
                  setEndOpen(true);
                }}
              >
                结束会话
              </Button>
              <Popconfirm
                title="取消会话？"
                description="取消后该会话将标记为 cancelled，不保存摘要。"
                onConfirm={() =>
                  cancelMutation.mutate(session.id, {
                    onSuccess: () => navigate('/teaching'),
                  })
                }
              >
                <Button danger icon={<StopOutlined />}>
                  取消
                </Button>
              </Popconfirm>
            </>
          )}
        </div>

        <PipelineProgress
          pipelineStatus={session.pipeline_status}
          messages={visibleMessages}
        />

        <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
          {visibleMessages.map((m) => (
            <ChatBubble key={m.id} message={m} />
          ))}
          {sending && (
            <ChatBubble
              streaming
              message={{
                id: -1,
                session_id: session.id,
                role: 'assistant',
                content: streamingText,
                message_type: 'chat',
                sequence: 9999,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              }}
            />
          )}
          <div ref={bottomRef} />
        </div>

        <ChatInput
          loading={sending}
          disabled={!isActive || !pipelineDone}
          onSend={handleSend}
          placeholder={
            !pipelineDone
              ? '讲解生成中，稍候即可追问...'
              : isActive
                ? '继续追问...'
                : '会话已结束，无法发送消息'
          }
        />
      </div>
    );

    rightContent = <StrategyPanel session={session} />;
  }

  return (
    <Row gutter={0} style={{ height: 'calc(100vh - 64px)' }}>
      <Col span={5} style={{ height: '100%' }}>
        <SessionHistorySidebar studentId={student.id} activeSessionId={activeSessionId} />
      </Col>

      <Col span={rightContent ? 12 : 19} style={{ height: '100%' }}>
        {centerContent}
      </Col>

      {rightContent && (
        <Col span={7} style={{ background: '#fff', borderLeft: '1px solid #f0f0f0', height: '100%' }}>
          {rightContent}
        </Col>
      )}

      <Modal
        open={endOpen}
        title="结束教学会话"
        onCancel={() => setEndOpen(false)}
        onOk={() =>
          sessionQuery.data &&
          endMutation.mutate({
            session_id: sessionQuery.data.id,
            mastery_level_delta: mastery,
          })
        }
        okText="确认结束"
        confirmLoading={endMutation.isPending}
      >
        <Typography.Paragraph>
          可选地提交一次掌握度调整（-1 ~ 1），用于聚合学生档案。
        </Typography.Paragraph>
        <Slider
          min={-1}
          max={1}
          step={0.1}
          value={mastery}
          onChange={(v) => setMastery(v as number)}
          marks={{ '-1': '明显下降', 0: '无变化', 1: '明显提升' }}
        />
      </Modal>
    </Row>
  );
}

function StartSessionView({
  onSubmit,
  loading,
}: {
  onSubmit: (body: {
    student_id: number;
    question_content: string;
    question_image?: string | null;
  }) => void;
  loading?: boolean;
}) {
  const student = useStudentStore((s) => s.current);
  const [form] = Form.useForm<{ content: string; image?: string }>();

  if (!student) return null;

  return (
    <div className="page-container" style={{ maxWidth: 800 }}>
      <Typography.Title level={3}>提交新题目</Typography.Title>
      <Typography.Paragraph type="secondary">
        输入题目文本（必要时附图片 URL），提交后 AI 将根据你的学习画像进行个性化讲解。
      </Typography.Paragraph>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) =>
            onSubmit({
              student_id: student.id,
              question_content: values.content,
              question_image: values.image || null,
            })
          }
        >
          <Form.Item
            label="题目内容"
            name="content"
            rules={[{ required: true, message: '请输入题目内容' }]}
          >
            <Input.TextArea rows={6} placeholder="请在此输入题目文本..." />
          </Form.Item>
          <Form.Item label="题目图片 URL（可选）" name="image">
            <Input placeholder="https://..." />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} size="large">
            提交并开始讲解
          </Button>
        </Form>
      </Card>
    </div>
  );
}
