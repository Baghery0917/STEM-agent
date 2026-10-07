import { apiClient } from './client';
import type { Persona } from './types';

export interface StudentCard {
  card_key: Persona;
  acquired_at: string;
}

export interface StudentBadge {
  badge_key: string;
  acquired_at: string;
}

export interface BadgeProgress {
  badge_key: string;
  metric: string;
  threshold: number;
  value: number;
}

export interface StudentCards {
  cards: StudentCard[];
  unlocked: Persona[];
  badges: StudentBadge[];
  badge_progress: BadgeProgress[];
}

export interface CheckinResponse {
  login_count: number;
  new_badges: StudentBadge[];
}

export async function getStudentCards(studentId: number) {
  const { data } = await apiClient.get<StudentCards>(`/students/${studentId}/cards`);
  return data;
}

export async function checkin(studentId: number) {
  const { data } = await apiClient.post<CheckinResponse>(`/students/${studentId}/checkin`);
  return data;
}
