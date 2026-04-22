import { apiClient } from './client';
import type {
  QuestionCreate,
  QuestionListParams,
  QuestionResponse,
  QuestionUpdate,
} from './types';

export async function listQuestions(params?: QuestionListParams) {
  const { data } = await apiClient.get<QuestionResponse[]>('/questions', {
    params,
    paramsSerializer: {
      indexes: null,
    },
  });
  return data;
}

export async function getQuestion(id: number) {
  const { data } = await apiClient.get<QuestionResponse>(`/questions/${id}`);
  return data;
}

export async function createQuestion(body: QuestionCreate) {
  const { data } = await apiClient.post<QuestionResponse>('/questions', body);
  return data;
}

export async function updateQuestion(id: number, body: QuestionUpdate) {
  const { data } = await apiClient.put<QuestionResponse>(`/questions/${id}`, body);
  return data;
}

export async function deleteQuestion(id: number) {
  await apiClient.delete(`/questions/${id}`);
}

export interface BulkImportQuestionsResult {
  created: number;
  errors: Array<{ index: number; message: string }>;
}

// TODO: 后端未实现 /questions/bulk，当前用顺序 POST
export async function bulkImportQuestions(
  items: QuestionCreate[],
): Promise<BulkImportQuestionsResult> {
  const result: BulkImportQuestionsResult = { created: 0, errors: [] };
  for (const [i, body] of items.entries()) {
    try {
      await createQuestion(body);
      result.created += 1;
    } catch (e) {
      result.errors.push({ index: i, message: (e as Error).message });
    }
  }
  return result;
}
