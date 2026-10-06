import { apiClient } from './client';
import type {
  ChatRequest,
  EndSessionRequest,
  RateMessageRequest,
  SubmitQuestionRequest,
  TeachingMessageResponse,
  TeachingChatResponse,
  TeachingSessionDetailResponse,
  TeachingSessionSummaryResponse,
} from './types';

export async function startTeachingSession(body: SubmitQuestionRequest) {
  const { data } = await apiClient.post<TeachingSessionDetailResponse>(
    '/teaching/sessions',
    body,
  );
  return data;
}

export async function chat(body: ChatRequest) {
  const { data } = await apiClient.post<TeachingChatResponse>(
    '/teaching/sessions/chat',
    body,
  );
  return data;
}

export type ChatStreamHandlers = {
  onDelta: (text: string) => void;
  onDone: () => void;
  onError: (msg: string) => void;
};

export async function streamChat(
  body: ChatRequest,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const base = (apiClient.defaults.baseURL ?? '/api/v1').replace(/\/$/, '');
  const resp = await fetch(`${base}/teaching/sessions/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  if (!resp.ok) {
    const text = await resp.text();
    handlers.onError(text || `HTTP ${resp.status}`);
    return;
  }
  if (!resp.body) {
    handlers.onError('No response body');
    return;
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const events = buf.split('\n\n');
      buf = events.pop() ?? '';
      for (const ev of events) {
        let eventType = 'message';
        let data = '';
        for (const line of ev.split('\n')) {
          if (line.startsWith('event: ')) eventType = line.slice(7).trim();
          else if (line.startsWith('data: ')) data = line.slice(6);
        }
        if (eventType === 'done') {
          handlers.onDone();
          return;
        }
        if (eventType === 'error') {
          let detail = data;
          try {
            const parsed = JSON.parse(data);
            if (parsed?.detail) detail = parsed.detail;
          } catch {
            /* keep raw */
          }
          handlers.onError(detail || 'stream error');
          return;
        }
        try {
          const obj = JSON.parse(data);
          if (obj?.delta) handlers.onDelta(obj.delta);
        } catch {
          /* ignore bad chunk */
        }
      }
    }
    handlers.onDone();
  } catch (err) {
    handlers.onError((err as Error).message || 'stream aborted');
  }
}

export async function rateMessage(body: RateMessageRequest) {
  const { data } = await apiClient.post<TeachingMessageResponse>('/teaching/sessions/rate', body);
  return data;
}

export async function endTeachingSession(body: EndSessionRequest) {
  const { data } = await apiClient.post<TeachingSessionDetailResponse>(
    '/teaching/sessions/end',
    body,
  );
  return data;
}

export async function cancelTeachingSession(sessionId: number) {
  const { data } = await apiClient.post<TeachingSessionDetailResponse>(
    `/teaching/sessions/${sessionId}/cancel`,
  );
  return data;
}

export async function getTeachingSession(sessionId: number) {
  const { data } = await apiClient.get<TeachingSessionDetailResponse>(
    `/teaching/sessions/${sessionId}`,
  );
  return data;
}

export async function listTeachingSessions(
  studentId: number,
  limit = 20,
  offset = 0,
) {
  const { data } = await apiClient.get<TeachingSessionSummaryResponse[]>(
    '/teaching/sessions',
    { params: { student_id: studentId, limit, offset } },
  );
  return data;
}
