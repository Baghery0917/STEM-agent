import { apiClient } from './client';
import type { ReportMode, SessionSearchResponse, StudentEvaluation, StudentReport } from './types';

export async function getStudentReport(studentId: number, mode: ReportMode, summary = true) {
  const { data } = await apiClient.get<StudentReport>(`/students/${studentId}/report`, {
    params: { mode, summary },
  });
  return data;
}

export async function getStudentEvaluation(studentId: number) {
  const { data } = await apiClient.get<StudentEvaluation>(`/students/${studentId}/evaluation`);
  return data;
}

export async function searchSessions(studentId: number, q: string, limit = 20) {
  const { data } = await apiClient.get<SessionSearchResponse>(`/students/${studentId}/sessions/search`, {
    params: { q, limit },
  });
  return data;
}
