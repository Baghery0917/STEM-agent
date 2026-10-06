import { apiClient } from './client';
import type { ReportMode, StudentReport } from './types';

export async function getStudentReport(studentId: number, mode: ReportMode, summary = true) {
  const { data } = await apiClient.get<StudentReport>(`/students/${studentId}/report`, {
    params: { mode, summary },
  });
  return data;
}
