import { apiClient } from './client';
import type { Gender, StudentCreate, StudentResponse, StudentUpdate } from './types';

export async function listStudents(params?: {
  skip?: number;
  limit?: number;
  gender?: Gender;
}) {
  const { data } = await apiClient.get<StudentResponse[]>('/students', { params });
  return data;
}

export async function getStudent(id: number) {
  const { data } = await apiClient.get<StudentResponse>(`/students/${id}`);
  return data;
}

export async function createStudent(body: StudentCreate) {
  const { data } = await apiClient.post<StudentResponse>('/students', body);
  return data;
}

export async function updateStudent(id: number, body: StudentUpdate) {
  const { data } = await apiClient.put<StudentResponse>(`/students/${id}`, body);
  return data;
}

export async function deleteStudent(id: number) {
  await apiClient.delete(`/students/${id}`);
}
