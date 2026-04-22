import { apiClient } from './client';

export async function ping(): Promise<{ status: string }> {
  const { data } = await apiClient.get('/health');
  return data;
}

export async function pingDb(): Promise<{ status: string; database: string }> {
  const { data } = await apiClient.get('/health/db');
  return data;
}
