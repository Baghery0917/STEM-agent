import type { ReportMode, StudentReport } from './types';

// TODO: 后端尚未实现 GET /students/:id/report?mode=recent|all
// 函数签名已固定，后端接入时替换实现体即可
export async function getStudentReport(
  _studentId: number,
  mode: ReportMode,
): Promise<StudentReport> {
  return {
    mode,
    active_knowledge_points: [],
    emotion_logs: [],
  };
}
