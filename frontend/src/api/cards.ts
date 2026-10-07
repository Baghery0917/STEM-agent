import { apiClient } from './client';
import type { Persona } from './types';

export interface StudentCard {
  card_key: Persona;
  acquired_at: string;
}

export interface StudentCards {
  cards: StudentCard[];
  unlocked: Persona[];
}

export async function getStudentCards(studentId: number) {
  const { data } = await apiClient.get<StudentCards>(`/students/${studentId}/cards`);
  return data;
}
