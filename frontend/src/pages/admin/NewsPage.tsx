import { App, Button, Card, DatePicker, Form, Input, Modal, Popconfirm, Space, Switch, Table, Tag, Typography } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs, { type Dayjs } from 'dayjs';
import { createNews, deleteNews, listAllNews, updateNews, type NewsInput, type NewsItem } from '@/api/news';
import { formatDateTime } from '@/utils/format';

type FormValues = Omit<NewsInput, 'published_on'> & { published_on: Dayjs };

const TAG_HINT = 'Nobel / Quantum / Plasma / Superconductivity / Photonics …';

export default function NewsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<NewsItem | null>(null);
  const [form] = Form.useForm<FormValues>();
  const qc = useQueryClient();
  const { message } = App.useApp();

  const query = useQuery({ queryKey: ['admin-news'], queryFn: listAllNews });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['admin-news'] });
    qc.invalidateQueries({ queryKey: ['public-news'] });
  };

  const save = useMutation({
    mutationFn: (v: FormValues) => {
      const body: NewsInput = { ...v, published_on: v.published_on.format('YYYY-MM-DD') };
      return editing ? updateNews(editing.id, body) : createNews(body);
    },
    onSuccess: () => { message.success(editing ? '已更新' : '已发布'); invalidate(); setFormOpen(false); },
    onError: (e: Error) => message.error(e.message),
  });
  const toggle = useMutation({
    mutationFn: (n: NewsItem) => updateNews(n.id, { published: !n.published }),
    onSuccess: invalidate,
    onError: (e: Error) => message.error(e.message),
  });
  const remove = useMutation({
    mutationFn: deleteNews,
    onSuccess: () => { message.success('已删除'); invalidate(); },
    onError: (e: Error) => message.error(e.message),
  });

  useEffect(() => {
    if (!formOpen) return;
    if (editing) form.setFieldsValue({ ...editing, published_on: dayjs(editing.published_on) });
    else { form.resetFields(); form.setFieldsValue({ published: true, published_on: dayjs() }); }
  }, [formOpen, editing, form]);

  return (
    <>
      <Typography.Title level={3} style={{ marginBottom: 16 }}>物理新闻</Typography.Title>
      <Typography.Paragraph type="secondary">落地页「物理界的新闻」板块。按发布日期倒序，只有「已发布」的会公开显示；后端没有数据时落地页回退到内置的几条。</Typography.Paragraph>
      <Card
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); setFormOpen(true); }}>新建</Button>}
      >
        <Table<NewsItem>
          rowKey="id"
          dataSource={query.data ?? []}
          loading={query.isLoading}
          pagination={{ pageSize: 20 }}
          columns={[
            { title: '日期', dataIndex: 'published_on', width: 120 },
            { title: '标签', dataIndex: 'tag', width: 140, render: (t: string) => <Tag>{t}</Tag> },
            {
              title: '标题',
              dataIndex: 'title',
              render: (t: string, r) => (
                <Space direction="vertical" size={2}>
                  <a href={r.url} target="_blank" rel="noreferrer">{t}</a>
                  <Typography.Text type="secondary" ellipsis style={{ maxWidth: 560 }}>{r.summary}</Typography.Text>
                </Space>
              ),
            },
            { title: '来源', dataIndex: 'source', width: 160 },
            {
              title: '公开',
              dataIndex: 'published',
              width: 90,
              render: (v: boolean, r) => <Switch checked={v} loading={toggle.isPending} onChange={() => toggle.mutate(r)} />,
            },
            { title: '更新', dataIndex: 'updated_at', width: 160, render: (v: string | null) => formatDateTime(v) },
            {
              title: '操作',
              width: 160,
              render: (_, r) => (
                <Space>
                  <Button type="link" icon={<EditOutlined />} onClick={() => { setEditing(r); setFormOpen(true); }}>编辑</Button>
                  <Popconfirm title="确认删除？" onConfirm={() => remove.mutate(r.id)}>
                    <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
                  </Popconfirm>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        open={formOpen}
        title={editing ? '编辑新闻' : '新建新闻'}
        onCancel={() => setFormOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={save.isPending}
        width={640}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={(v) => save.mutate(v)}>
          <Form.Item label="标题" name="title" rules={[{ required: true, message: '请输入标题' }]}>
            <Input maxLength={200} placeholder="一句话说清楚发生了什么" />
          </Form.Item>
          <Form.Item label="摘要" name="summary" rules={[{ required: true, message: '请输入摘要' }]}>
            <Input.TextArea rows={4} placeholder="两三句，能在课上讲清楚的程度" />
          </Form.Item>
          <Space size={16} style={{ display: 'flex' }} align="start">
            <Form.Item label="标签" name="tag" rules={[{ required: true }]} style={{ flex: 1 }}>
              <Input maxLength={40} placeholder={TAG_HINT} />
            </Form.Item>
            <Form.Item label="日期" name="published_on" rules={[{ required: true }]}>
              <DatePicker />
            </Form.Item>
            <Form.Item label="公开" name="published" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Space>
          <Form.Item label="来源" name="source" rules={[{ required: true }]}>
            <Input maxLength={120} placeholder="nobelprize.org / phys.org / Nature …" />
          </Form.Item>
          <Form.Item label="链接" name="url" rules={[{ required: true, type: 'url', message: '需要完整 URL' }]}>
            <Input placeholder="https://…" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
