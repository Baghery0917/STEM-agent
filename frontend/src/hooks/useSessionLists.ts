import { useQuery } from '@tanstack/react-query';
import { listTeachingSessions } from '@/api/teaching';
import { listPracticeSessions } from '@/api/practice';
import type { PracticeSessionResponse, TeachingSessionSummaryResponse } from '@/api/types';

export type RailItem =
  | { kind: 'teaching'; id: number; at: string; data: TeachingSessionSummaryResponse }
  | { kind: 'practice'; id: number; at: string; data: PracticeSessionResponse };

export function useTeachingSessions(studentId?: number) {
  return useQuery({
    queryKey: ['teaching-sessions', studentId],
    queryFn: () => listTeachingSessions(studentId!, 50, 0),
    enabled: !!studentId,
  });
}

export function usePracticeSessions(studentId?: number) {
  return useQuery({
    queryKey: ['practice-sessions', studentId],
    queryFn: () => listPracticeSessions(studentId!, 50, 0),
    enabled: !!studentId,
  });
}

/** 教学与练习会话合并后按时间倒序，供左侧会话栏使用 */
export function useRailItems(studentId?: number) {
  const teaching = useTeachingSessions(studentId);
  const practice = usePracticeSessions(studentId);
  const items: RailItem[] = [
    ...(teaching.data ?? []).map<RailItem>((s) => ({
      kind: 'teaching', id: s.id, at: s.created_at ?? '', data: s,
    })),
    ...(practice.data ?? []).map<RailItem>((s) => ({
      kind: 'practice', id: s.id, at: s.started_at, data: s,
    })),
  ].sort((a, b) => (b.at > a.at ? 1 : b.at < a.at ? -1 : 0));
  return { items, isLoading: teaching.isLoading || practice.isLoading };
}
