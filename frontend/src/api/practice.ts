import { apiClient } from './client';
import type {
  PracticeMatchRequest,
  PracticeMatchResponse,
  PracticeSessionDetailResponse,
  PracticeSessionResponse,
  SkipQuestionRequest,
  SkipQuestionResponse,
  StarQuestionRequest,
  StartPracticeRequest,
  StartSessionResponse,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from './types';

export async function matchPractice(body: PracticeMatchRequest) {
  const { data } = await apiClient.post<PracticeMatchResponse>('/practice/match', body);
  return data;
}

export async function startPractice(body: StartPracticeRequest) {
  const { data } = await apiClient.post<StartSessionResponse>('/practice/sessions', body);
  return data;
}

export async function submitAnswer(sessionId: number, body: SubmitAnswerRequest) {
  const { data } = await apiClient.post<SubmitAnswerResponse>(
    `/practice/sessions/${sessionId}/submit`,
    body,
  );
  return data;
}

export async function skipQuestion(sessionId: number, body: SkipQuestionRequest) {
  const { data } = await apiClient.post<SkipQuestionResponse>(
    `/practice/sessions/${sessionId}/skip`,
    body,
  );
  return data;
}

export async function starQuestion(sessionId: number, body: StarQuestionRequest) {
  const { data } = await apiClient.post<PracticeSessionResponse>(
    `/practice/sessions/${sessionId}/star`,
    body,
  );
  return data;
}

export async function endPractice(sessionId: number) {
  const { data } = await apiClient.post<PracticeSessionResponse>(
    `/practice/sessions/${sessionId}/end`,
  );
  return data;
}

export async function getPracticeSession(sessionId: number) {
  const { data } = await apiClient.get<PracticeSessionDetailResponse>(
    `/practice/sessions/${sessionId}`,
  );
  return data;
}

export async function listPracticeSessions(studentId: number, limit = 20, offset = 0) {
  const { data } = await apiClient.get<PracticeSessionResponse[]>('/practice/sessions', {
    params: { student_id: studentId, limit, offset },
  });
  return data;
}
