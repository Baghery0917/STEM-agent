import { apiClient } from './client';

const TOKEN_KEY = 'stem:admin-token';

export function getAdminToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function clearAdminToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

export async function adminLogin(password: string) {
  const { data } = await apiClient.post<{ token: string }>('/admin/login', { password });
  sessionStorage.setItem(TOKEN_KEY, data.token);
  return data.token;
}

// 管理台请求统一带口令令牌
apiClient.interceptors.request.use((config) => {
  if (config.url?.startsWith('/admin/db') || config.url?.startsWith('/admin/news')) {
    const token = getAdminToken();
    if (token) config.headers.set('X-Admin-Token', token);
  }
  return config;
});

export interface AdminDbColumn {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

export interface AdminDbTable {
  name: string;
  columns: AdminDbColumn[];
  row_count: number;
}

export interface AdminDbRowsResponse {
  table: string;
  columns: AdminDbColumn[];
  rows: Record<string, unknown>[];
  total: number;
}

export interface QueryDbTableParams {
  limit?: number;
  offset?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export async function listDbTables() {
  const { data } = await apiClient.get<AdminDbTable[]>('/admin/db/tables');
  return data;
}

export async function queryDbTable(name: string, params: QueryDbTableParams = {}) {
  const { data } = await apiClient.get<AdminDbRowsResponse>(
    `/admin/db/tables/${encodeURIComponent(name)}`,
    { params },
  );
  return data;
}
