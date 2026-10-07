import { useQuery } from '@tanstack/react-query';
import { getStudentCards } from '@/api/cards';

export function useCards(studentId?: number) {
  return useQuery({
    queryKey: ['student-cards', studentId],
    queryFn: () => getStudentCards(studentId!),
    enabled: !!studentId,
    staleTime: 30_000,
  });
}
