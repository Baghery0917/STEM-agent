import { App, Button, Card, Form, Input, Modal, Popconfirm, Radio, Select, Space, Table, Tag, Typography } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createStudent,
  deleteStudent,
  listStudents,
  updateStudent,
} from '@/api/students';
import type { Gender, StudentResponse } from '@/api/types';
import { GENDER_LABEL, GENDER_OPTIONS } from '@/utils/enums';
import { formatDateTime } from '@/utils/format';

export default function StudentsPage() {
  const [genderFilter, setGenderFilter] = useState<Gender | undefined>();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<StudentResponse | null>(null);
  const [form] = Form.useForm<{ name: string; gender: Gender }>();
  const queryClient = useQueryClient();
  const { message } = App.useApp();

  const query = useQuery({
    queryKey: ['students', { gender: genderFilter }],
    queryFn: () => listStudents({ gender: genderFilter, limit: 100 }),
  });

  const saveMutation = useMutation({
    mutationFn: async (values: { name: string; gender: Gender }) => {
      if (editing) return updateStudent(editing.id, values);
      return createStudent(values);
    },
    onSuccess: () => {
      message.success(editing ? '已更新' : '已创建');
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setFormOpen(false);
    },
    onError: (err: Error) => message.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteStudent(id),
    onSuccess: () => {
      message.success('已删除');
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
    onError: (err: Error) => message.error(err.message),
  });

  useEffect(() => {
    if (!formOpen) return;
    if (editing) {
      form.setFieldsValue({ name: editing.name, gender: editing.gender });
    } else {
      form.resetFields();
      form.setFieldsValue({ gender: 'male' });
    }
  }, [formOpen, editing, form]);

  return (
    <>
      <Typography.Title level={3} style={{ marginBottom: 16 }}>
        学生管理
      </Typography.Title>
      <Card
        title={
          <Space>
            <span>性别筛选：</span>
            <Select
              placeholder="全部"
              allowClear
              options={GENDER_OPTIONS}
              value={genderFilter}
              onChange={setGenderFilter}
              style={{ width: 140 }}
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
            新建学生
          </Button>
        }
      >
        <Table<StudentResponse>
          rowKey="id"
          dataSource={query.data ?? []}
          loading={query.isLoading}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 80 },
            { title: '姓名', dataIndex: 'name' },
            {
              title: '性别',
              dataIndex: 'gender',
              width: 100,
              render: (g: Gender) => <Tag>{GENDER_LABEL[g]}</Tag>,
            },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              width: 180,
              render: (v: string | null) => formatDateTime(v),
            },
            {
              title: '操作',
              width: 160,
              render: (_, record) => (
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
                    title="确认删除？"
                    onConfirm={() => deleteMutation.mutate(record.id)}
                  >
                    <Button type="link" danger icon={<DeleteOutlined />}>
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        open={formOpen}
        title={editing ? '编辑学生' : '新建学生'}
        onCancel={() => setFormOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saveMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={(v) => saveMutation.mutate(v)}>
          <Form.Item
            label="姓名"
            name="name"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input maxLength={100} />
          </Form.Item>
          <Form.Item label="性别" name="gender" rules={[{ required: true }]}>
            <Radio.Group>
              <Radio value="male">男</Radio>
              <Radio value="female">女</Radio>
              <Radio value="other">其他</Radio>
            </Radio.Group>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
