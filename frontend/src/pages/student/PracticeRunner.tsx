import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  App,
  Button,
  Card,
  Col,
  Divider,
  Progress,
  Result,
  Row,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ForwardOutlined,
  SendOutlined,
} from '@ant-design/icons';
import {
  endPractice,
  getPracticeSession,
  nextQuestion,
  skipQuestion,
  submitAnswer,
} from '@/api/practice';
import type {
  PracticeSessionDetailResponse,
  PracticeSessionResponse,
  QuestionResponse,
  StartSessionResponse,
  SubmitAnswerResponse,
} from '@/api/types';
import QuestionView from '@/components/practice/QuestionView';
import ResultFeedback from '@/components/practice/ResultFeedback';
import ThinkingTimer from '@/components/practice/ThinkingTimer';
import PracticeReviewView from '@/components/practice/PracticeReviewView';
import { DIFFICULTY_COLOR, DIFFICULTY_LABEL, QUESTION_TYPE_LABEL } from '@/utils/enums';

type Phase = 'answering' | 'feedback' | 'done';

export default function PracticeRunner() {
  const { sessionId: sessionIdParam } = useParams<{ sessionId: string }>();
  const sessionId = Number(sessionIdParam);
  const location = useLocation();
  const navigate = useNavigate();
  const { message } = App.useApp();

  const initialData = location.state as StartSessionResponse | undefined;

  const [session, setSession] = useState<PracticeSessionResponse | null>(
    initialData?.session ?? null,
  );
  const [currentQuestion, setCurrentQuestion] = useState<QuestionResponse | null>(
    initialData?.question ?? null,
  );
  const [answer, setAnswer] = useState('');
  const [phase, setPhase] = useState<Phase>('answering');
  const [lastResult, setLastResult] = useState<SubmitAnswerResponse | null>(null);
  const [startedAt, setStartedAt] = useState<number>(Date.now());

  const sessionDetailQuery = useQuery({
    queryKey: ['practice-session', sessionId],
    queryFn: () => getPracticeSession(sessionId),
    enabled: !!sessionId && !session,
  });

  useEffect(() => {
    if (!session && sessionDetailQuery.data) {
      setSession(sessionDetailQuery.data);
    }
  }, [sessionDetailQuery.data, session]);

  useEffect(() => {
    setStartedAt(Date.now());
    setAnswer('');
    setPhase('answering');
  }, [currentQuestion?.id]);

  const submitMutation = useMutation({
    mutationFn: (payload: { user_answer: string }) =>
      submitAnswer(sessionId, {
        question_id: currentQuestion!.id,
        user_answer: payload.user_answer,
      }),
    onSuccess: (data) => {
      setLastResult(data);
      setPhase('feedback');
      setSession((prev) =>
        prev
          ? {
              ...prev,
              correct_count: prev.correct_count + (data.is_correct ? 1 : 0),
              wrong_count: prev.wrong_count + (data.is_correct ? 0 : 1),
            }
          : prev,
      );
    },
    onError: (err: Error) => message.error(err.message),
  });

  const skipMutation = useMutation({
    mutationFn: () => skipQuestion(sessionId, { question_id: currentQuestion!.id }),
    onSuccess: (data) => {
      setSession((prev) =>
        prev ? { ...prev, skip_count: prev.skip_count + 1 } : prev,
      );
      if (data.question) {
        setCurrentQuestion(data.question);
      } else {
        setPhase('done');
      }
    },
    onError: (err: Error) => message.error(err.message),
  });

  const nextMutation = useMutation({
    mutationFn: () => nextQuestion(sessionId),
    onSuccess: (data) => {
      if (data.question) setCurrentQuestion(data.question);
      else setPhase('done');
    },
    onError: (err: Error) => message.error(err.message),
  });

  const endMutation = useMutation({
    mutationFn: () => endPractice(sessionId),
    onSuccess: (data) => {
      setSession(data);
      setPhase('done');
    },
    onError: (err: Error) => message.error(err.message),
  });

  const isFocused = session?.mode === 'focused';
  const totalAnswered = (session?.correct_count ?? 0) + (session?.wrong_count ?? 0);
  const progressPercent = useMemo(() => {
    if (!session) return 0;
    if (isFocused && session.total_count > 0) {
      return Math.round((totalAnswered / session.total_count) * 100);
    }
    return totalAnswered > 0 ? 100 : 0;
  }, [session, totalAnswered, isFocused]);

  if (!initialData && sessionDetailQuery.data?.ended_at) {
    return <PracticeReviewView session={sessionDetailQuery.data as PracticeSessionDetailResponse} />;
  }

  if (!session || (!currentQuestion && phase === 'answering' && !initialData)) {
    if (sessionDetailQuery.isLoading) {
      return (
        <div style={{ textAlign: 'center', padding: 64 }}>
          <Spin />
        </div>
      );
    }
  }

  if (phase === 'done' && session) {
    return (
      <div className="page-container" style={{ maxWidth: 720 }}>
        <Result
          status="success"
          title="本次练习已完成"
          subTitle={`共作答 ${session.correct_count + session.wrong_count} 题，正确 ${
            session.correct_count
          } 题。`}
        />
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic title="正确" value={session.correct_count} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="错误" value={session.wrong_count} valueStyle={{ color: '#ff4d4f' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="跳过" value={session.skip_count} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="模式" value={session.mode} />
            </Card>
          </Col>
        </Row>
        <Space style={{ marginTop: 24 }}>
          <Button type="primary" onClick={() => navigate('/practice/setup')}>
            再来一组
          </Button>
          <Button onClick={() => navigate('/home')}>返回首页</Button>
        </Space>
      </div>
    );
  }

  if (!session || !currentQuestion) {
    return (
      <div style={{ textAlign: 'center', padding: 64 }}>
        <Spin />
      </div>
    );
  }

  const handleSubmit = () => {
    if (!answer.trim()) {
      message.warning('请先作答');
      return;
    }
    submitMutation.mutate({ user_answer: answer.trim() });
  };

  const handleNext = () => {
    if (!lastResult) return;
    if (lastResult.next_question) {
      setCurrentQuestion(lastResult.next_question);
      setLastResult(null);
    } else if (isFocused) {
      endMutation.mutate();
    } else {
      nextMutation.mutate();
    }
  };

  return (
    <div className="page-container" style={{ maxWidth: 900 }}>
      <Card
        style={{ marginBottom: 16 }}
        extra={
          <Space>
            <Tag color={isFocused ? 'blue' : 'geekblue'}>
              {isFocused ? 'Focused' : 'General'}
            </Tag>
            <Button size="small" danger onClick={() => endMutation.mutate()} loading={endMutation.isPending}>
              结束练习
            </Button>
          </Space>
        }
      >
        <Row align="middle" gutter={16}>
          <Col flex="auto">
            <Typography.Text type="secondary">进度</Typography.Text>
            <Progress
              percent={progressPercent}
              status="active"
              format={() =>
                isFocused
                  ? `${totalAnswered} / ${session.total_count}`
                  : `已作答 ${totalAnswered}`
              }
            />
          </Col>
          <Col>
            <ThinkingTimer startedAt={startedAt} running={phase === 'answering'} />
          </Col>
        </Row>
      </Card>

      <Card
        title={
          <Space>
            <Typography.Text strong>第 {totalAnswered + session.skip_count + 1} 题</Typography.Text>
            <Tag>{QUESTION_TYPE_LABEL[currentQuestion.type]}</Tag>
            <Tag color={DIFFICULTY_COLOR[currentQuestion.difficulty]}>
              {DIFFICULTY_LABEL[currentQuestion.difficulty]}
            </Tag>
          </Space>
        }
      >
        <QuestionView
          question={currentQuestion}
          value={answer}
          onChange={setAnswer}
          disabled={phase === 'feedback'}
        />
        <Divider />
        {phase === 'answering' ? (
          <Space>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSubmit}
              loading={submitMutation.isPending}
            >
              提交答案
            </Button>
            {!isFocused && (
              <Button
                icon={<ForwardOutlined />}
                onClick={() => skipMutation.mutate()}
                loading={skipMutation.isPending}
              >
                跳过本题
              </Button>
            )}
          </Space>
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {lastResult && (
              <ResultFeedback item={lastResult.item} question={currentQuestion} />
            )}
            <Space>
              <Button
                type="primary"
                icon={lastResult?.is_correct ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                onClick={handleNext}
                loading={nextMutation.isPending || endMutation.isPending}
              >
                {isFocused && !lastResult?.next_question ? '查看总结' : '下一题'}
              </Button>
              {!isFocused && (
                <Button onClick={() => endMutation.mutate()} loading={endMutation.isPending}>
                  结束练习
                </Button>
              )}
            </Space>
          </Space>
        )}
      </Card>
    </div>
  );
}
