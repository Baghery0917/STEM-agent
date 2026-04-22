import { App, Button, Card, Popconfirm, Select, Space, Table, Tag, Typography } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteQuestion, listQuestions } from '@/api/questions';
import type {
  Difficulty,
  QuestionResponse,
  QuestionType,
} from '@/api/types';
import QuestionForm from '@/components/questions/QuestionForm';
import { useKnowledgeTree, buildSectionPath } from '@/hooks/useKnowledgeTree';
import {
  DIFFICULTY_COLOR,
  DIFFICULTY_LABEL,
  DIFFICULTY_OPTIONS,
  QUESTION_TYPE_LABEL,
  QUESTION_TYPE_OPTIONS,
} from '@/utils/enums';

export default function QuestionsPage() {
  const [type, setType] = useState<QuestionType | undefined>();
  const [difficulty, setDifficulty] = useState<Difficulty | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<QuestionResponse | null>(null);
  const queryClient = useQueryClient();
  const { message, modal } = App.useApp();
  const tree = useKnowledgeTree();

  const query = useQuery({
    queryKey: ['questions', { type, difficulty, page, pageSize }],
    queryFn: () =>
      listQuestions({
        type,
        difficulty,
        skip: (page - 1) * pageSize,
        limit: pageSize,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteQuestion(id),
    onSuccess: () => {
      message.success('已删除');
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
    onError: (err: Error) => message.error(err.message),
  });

  const columns = useMemo(
    () => [
      {
        title: 'ID',
        dataIndex: 'id',
        width: 70,
      },
      {
        title: '类型',
        dataIndex: 'type',
        width: 110,
        render: (t: QuestionType) => <Tag>{QUESTION_TYPE_LABEL[t]}</Tag>,
      },
      {
        title: '难度',
        dataIndex: 'difficulty',
        width: 90,
        render: (d: Difficulty) => (
          <Tag color={DIFFICULTY_COLOR[d]}>{DIFFICULTY_LABEL[d]}</Tag>
        ),
      },
      {
        title: '题目内容',
        dataIndex: 'content',
        ellipsis: true,
      },
      {
        title: '知识点',
        dataIndex: 'knowledge_point_ids',
        width: 260,
        render: (ids: number[]) =>
          tree.data
            ? ids.map((id) => (
                <Tag key={id} style={{ marginBottom: 2 }}>
                  {buildSectionPath(tree.data!, id)}
                </Tag>
              ))
            : ids.join(','),
      },
      {
        title: '操作',
        width: 150,
        render: (_: unknown, record: QuestionResponse) => (
          <Space>
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => {
                setEditing(record);
                setFormOpen(true);
              }}
            >
              编辑
            </Button>
            <Popconfirm
              title="确认删除此题目？"
              onConfirm={() => deleteMutation.mutate(record.id)}
            >
              <Button type="link" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [tree.data, deleteMutation],
  );

  return (
    <>
      <Typography.Title level={3} style={{ marginBottom: 16 }}>
        题库管理
      </Typography.Title>
      <Card
        style={{ marginBottom: 16 }}
        title={
          <Space wrap>
            <span>筛选：</span>
            <Select
              placeholder="类型"
              allowClear
              options={QUESTION_TYPE_OPTIONS}
              value={type}
              onChange={setType}
              style={{ width: 140 }}
            />
            <Select
              placeholder="难度"
              allowClear
              options={DIFFICULTY_OPTIONS}
              value={difficulty}
              onChange={setDifficulty}
              style={{ width: 120 }}
            />
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            新建题目
          </Button>
        }
      >
        <Table<QuestionResponse>
          rowKey="id"
          dataSource={query.data ?? []}
          columns={columns}
          loading={query.isLoading}
          pagination={{
            current: page,
            pageSize,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
            showSizeChanger: true,
          }}
        />
      </Card>

      <QuestionForm
        open={formOpen}
        initial={editing}
        onClose={() => setFormOpen(false)}
      />
    </>
  );
}
