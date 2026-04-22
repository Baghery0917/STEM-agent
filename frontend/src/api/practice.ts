import { apiClient } from './client';
import type {
  NextQuestionResponse,
  PracticeSessionDetailResponse,
  PracticeSessionResponse,
  SkipQuestionRequest,
  StartFocusedRequest,
  StartGeneralRequest,
  StartSessionResponse,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from './types';

export async function startFocused(body: StartFocusedRequest) {
  const { data } = await apiClient.post<StartSessionResponse>(
    '/practice/sessions/focused',
    body,
  );
  return data;
}

export async function startGeneral(body: StartGeneralRequest) {
  const { data } = await apiClient.post<StartSessionResponse>(
    '/practice/sessions/general',
    body,
  );
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
  const { data } = await apiClient.post<NextQuestionResponse>(
    `/practice/sessions/${sessionId}/skip`,
    body,
  );
  return data;
}

export async function nextQuestion(sessionId: number) {
  const { data } = await apiClient.post<NextQuestionResponse>(
    `/practice/sessions/${sessionId}/next`,
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

export async function listPracticeSessions(
  studentId: number,
  limit = 20,
  offset = 0,
) {
  const { data } = await apiClient.get<PracticeSessionResponse[]>(
    '/practice/sessions',
    { params: { student_id: studentId, limit, offset } },
  );
  return data;
}
