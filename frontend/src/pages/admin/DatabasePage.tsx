import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Card,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import type { SorterResult } from 'antd/es/table/interface';
import { listDbTables, queryDbTable } from '@/api/admin';
import type { AdminDbColumn, AdminDbRowsResponse } from '@/api/admin';

const SORTABLE_TYPE_RE = /^(INTEGER|BIGINT|SMALLINT|NUMERIC|FLOAT|REAL|DOUBLE|TIMESTAMP|DATE|TIME|BOOLEAN|UUID)/i;

function isSortable(col: AdminDbColumn): boolean {
  if (col.primary_key) return true;
  return SORTABLE_TYPE_RE.test(col.type);
}

function renderCell(value: unknown): React.ReactNode {
  if (value === null || value === undefined) {
    return <Typography.Text type="secondary">—</Typography.Text>;
  }
  if (typeof value === 'boolean') {
    return <Tag color={value ? 'green' : 'default'}>{String(value)}</Tag>;
  }
  if (typeof value === 'number') {
    return <span>{value}</span>;
  }
  const s = String(value);
  const looksTruncated = s.endsWith('…');
  const looksVector = /^vector\[\d+\]$/i.test(s);
  const looksJson = /^[\[{]/.test(s);
  if (looksVector) {
    return <Tag color="purple">{s}</Tag>;
  }
  if (looksJson || looksTruncated) {
    return (
      <Typography.Text
        style={{
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontSize: 12,
        }}
      >
        {s}
      </Typography.Text>
    );
  }
  return <span style={{ whiteSpace: 'pre-wrap' }}>{s}</span>;
}

export default function DatabasePage() {
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sort, setSort] = useState<string | null>(null);
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  const tablesQuery = useQuery({
    queryKey: ['admin-db-tables'],
    queryFn: listDbTables,
  });

  useEffect(() => {
    if (!selectedTable && tablesQuery.data && tablesQuery.data.length > 0) {
      setSelectedTable(tablesQuery.data[0].name);
    }
  }, [tablesQuery.data, selectedTable]);

  const rowsQuery = useQuery({
    queryKey: ['admin-db-rows', selectedTable, page, pageSize, sort, order],
    queryFn: () =>
      queryDbTable(selectedTable!, {
        limit: pageSize,
        offset: (page - 1) * pageSize,
        sort: sort ?? undefined,
        order,
      }),
    enabled: !!selectedTable,
  });

  const tableMeta = useMemo(
    () => tablesQuery.data?.find((t) => t.name === selectedTable),
    [tablesQuery.data, selectedTable],
  );

  const antdColumns: ColumnsType<Record<string, unknown>> = useMemo(() => {
    const cols = rowsQuery.data?.columns ?? tableMeta?.columns ?? [];
    return cols.map((col) => ({
      title: (
        <span>
          <span style={{ fontWeight: col.primary_key ? 700 : 500 }}>{col.name}</span>
          {!col.nullable && !col.primary_key && (
            <Typography.Text type="danger" style={{ marginLeft: 2 }}>
              *
            </Typography.Text>
          )}
          <Typography.Text
            type="secondary"
            style={{ marginLeft: 6, fontSize: 11, fontWeight: 'normal' }}
          >
            {col.type}
          </Typography.Text>
        </span>
      ),
      dataIndex: col.name,
      key: col.name,
      sorter: isSortable(col),
      sortOrder:
        sort === col.name ? (order === 'asc' ? 'ascend' : 'descend') : null,
      render: (v: unknown) => renderCell(v),
      ellipsis: true,
      width: col.primary_key ? 80 : 180,
    }));
  }, [rowsQuery.data, tableMeta, sort, order]);

  const handleTableChange = (
    pagination: TablePaginationConfig,
    _filters: unknown,
    sorter: SorterResult<Record<string, unknown>> | SorterResult<Record<string, unknown>>[],
  ) => {
    if (pagination.current) setPage(pagination.current);
    if (pagination.pageSize) setPageSize(pagination.pageSize);

    const single = Array.isArray(sorter) ? sorter[0] : sorter;
    if (single && single.order && single.field) {
      setSort(String(single.field));
      setOrder(single.order === 'ascend' ? 'asc' : 'desc');
    } else {
      setSort(null);
      setOrder('desc');
    }
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16,
          gap: 16,
        }}
      >
        <Typography.Title level={3} style={{ margin: 0 }}>
          数据库浏览
        </Typography.Title>
        <Space>
          <Select
            style={{ width: 280 }}
            placeholder="选择表"
            value={selectedTable}
            onChange={(v) => {
              setSelectedTable(v);
              setPage(1);
              setSort(null);
              setOrder('desc');
            }}
            loading={tablesQuery.isLoading}
            options={
              tablesQuery.data?.map((t) => ({
                value: t.name,
                label: (
                  <span>
                    {t.name}{' '}
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      ({t.row_count} 行)
                    </Typography.Text>
                  </span>
                ),
              })) ?? []
            }
          />
          <Typography.Text
            type="secondary"
            style={{ cursor: 'pointer' }}
            onClick={() => rowsQuery.refetch()}
          >
            <ReloadOutlined /> 刷新
          </Typography.Text>
        </Space>
      </div>

      {tablesQuery.isError && (
        <Alert type="error" message="加载表清单失败" showIcon style={{ marginBottom: 12 }} />
      )}
      {rowsQuery.isError && (
        <Alert type="error" message={(rowsQuery.error as Error)?.message ?? '查询失败'} showIcon style={{ marginBottom: 12 }} />
      )}

      <Card
        size="small"
        title={
          tableMeta ? (
            <Space>
              <span>
                <strong>{tableMeta.name}</strong>
              </span>
              <Typography.Text type="secondary">
                {tableMeta.columns.length} 列 / {tableMeta.row_count} 行
              </Typography.Text>
            </Space>
          ) : (
            '请选择表'
          )
        }
      >
        {!selectedTable ? (
          <div style={{ textAlign: 'center', padding: 48 }}>
            <Spin />
          </div>
        ) : (
          <Table<Record<string, unknown>>
            size="small"
            rowKey={(r, idx) => {
              const pk = rowsQuery.data?.columns.find((c) => c.primary_key);
              if (pk && r[pk.name] !== undefined) return String(r[pk.name]);
              return String(idx);
            }}
            loading={rowsQuery.isLoading || rowsQuery.isFetching}
            columns={antdColumns}
            dataSource={rowsQuery.data?.rows ?? []}
            scroll={{ x: 'max-content' }}
            pagination={{
              current: page,
              pageSize,
              total: rowsQuery.data?.total ?? 0,
              showSizeChanger: true,
              pageSizeOptions: [10, 20, 50, 100, 200],
              showTotal: (t) => `共 ${t} 行`,
            }}
            onChange={handleTableChange}
          />
        )}
      </Card>
    </div>
  );
}
