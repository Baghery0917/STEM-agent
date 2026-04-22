import { apiClient } from './client';

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
