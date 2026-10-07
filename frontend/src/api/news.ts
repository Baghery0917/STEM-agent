import { apiClient } from './client';
import type { Timestamps } from './types';

export interface NewsItem extends Timestamps {
  id: number;
  title: string;
  summary: string;
  tag: string;
  source: string;
  url: string;
  /** YYYY-MM-DD */
  published_on: string;
  published: boolean;
}

export type NewsInput = Omit<NewsItem, 'id' | 'created_at' | 'updated_at'>;

export async function listPublicNews(limit = 8) {
  const { data } = await apiClient.get<NewsItem[]>('/news', { params: { limit } });
  return data;
}

export async function listAllNews() {
  const { data } = await apiClient.get<NewsItem[]>('/admin/news');
  return data;
}

export async function createNews(body: NewsInput) {
  const { data } = await apiClient.post<NewsItem>('/admin/news', body);
  return data;
}

export async function updateNews(id: number, body: Partial<NewsInput>) {
  const { data } = await apiClient.put<NewsItem>(`/admin/news/${id}`, body);
  return data;
}

export async function deleteNews(id: number) {
  await apiClient.delete(`/admin/news/${id}`);
}
