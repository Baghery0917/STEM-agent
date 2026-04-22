import { App, Button, Form, Input, InputNumber, Space, Typography } from 'antd';
import { DeleteOutlined, SaveOutlined } from '@ant-design/icons';
import { useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createChapter,
  createSection,
  createVolume,
  deleteChapter,
  deleteSection,
  deleteVolume,
  updateChapter,
  updateSection,
  updateVolume,
} from '@/api/knowledge';
import type {
  ChapterResponse,
  SectionResponse,
  VolumeResponse,
} from '@/api/types';

export type NodeKind = 'volume' | 'chapter' | 'section';

export interface SelectedNode {
  kind: NodeKind;
  node: VolumeResponse | ChapterResponse | SectionResponse | null;
  parentId?: number;
}

interface Props {
  selected: SelectedNode | null;
}

export default function NodeEditForm({ selected }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const { message, modal } = App.useApp();

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['knowledge-tree'] });

  useEffect(() => {
    if (!selected?.node) {
      form.resetFields();
      return;
    }
    const n = selected.node;
    if (selected.kind === 'section') {
      form.setFieldsValue({
        title: (n as SectionResponse).title,
        content: (n as SectionResponse).content ?? '',
        order: n.order,
      });
    } else {
      form.setFieldsValue({
        title: (n as VolumeResponse | ChapterResponse).title,
        description:
          (n as VolumeResponse | ChapterResponse).description ?? '',
        order: n.order,
      });
    }
  }, [selected, form]);

  const saveMutation = useMutation({
    mutationFn: async (values: Record<string, unknown>) => {
      if (!selected || !selected.node) throw new Error('No node selected');
      const id = selected.node.id;
      if (selected.kind === 'volume') {
        if (id === -1)
          return createVolume(values as { title: string; description?: string; order?: number });
        return updateVolume(id, values);
      }
      if (selected.kind === 'chapter') {
        if (id === -1)
          return createChapter({
            volume_id: selected.parentId!,
            ...(values as { title: string; description?: string; order?: number }),
          });
        return updateChapter(id, values);
      }
      if (id === -1)
        return createSection({
          chapter_id: selected.parentId!,
          ...(values as { title: string; content?: string; order?: number }),
        });
      return updateSection(id, values);
    },
    onSuccess: () => {
      message.success('已保存');
      invalidate();
    },
    onError: (err: Error) => message.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!selected?.node) throw new Error('No node');
      if (selected.node.id === -1) return;
      if (selected.kind === 'volume') return deleteVolume(selected.node.id);
      if (selected.kind === 'chapter') return deleteChapter(selected.node.id);
      return deleteSection(selected.node.id);
    },
    onSuccess: () => {
      message.success('已删除');
      invalidate();
    },
    onError: (err: Error) => message.error(err.message),
  });

  if (!selected) {
    return (
      <Typography.Text type="secondary">请在左侧选择节点进行编辑，或点击节点上的 “+” 新增。</Typography.Text>
    );
  }

  const isSection = selected.kind === 'section';
  const isNew = selected.node?.id === -1;
  const kindLabel = { volume: '册', chapter: '章', section: '节' }[selected.kind];

  return (
    <div>
      <Typography.Title level={5}>
        {isNew ? `新建${kindLabel}` : `编辑${kindLabel}`}
      </Typography.Title>
      <Form form={form} layout="vertical" onFinish={(v) => saveMutation.mutate(v)}>
        <Form.Item
          label="标题"
          name="title"
          rules={[{ required: true, message: '请输入标题' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          label={isSection ? '内容 / 描述' : '描述'}
          name={isSection ? 'content' : 'description'}
        >
          <Input.TextArea autoSize={{ minRows: 3, maxRows: 8 }} />
        </Form.Item>
        <Form.Item label="排序" name="order" initialValue={0}>
          <InputNumber min={0} />
        </Form.Item>
        <Space>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            htmlType="submit"
            loading={saveMutation.isPending}
          >
            保存
          </Button>
          {!isNew && (
            <Button
              danger
              icon={<DeleteOutlined />}
              loading={deleteMutation.isPending}
              onClick={() =>
                modal.confirm({
                  title: `确认删除此${kindLabel}？`,
                  content: '删除后其下所有子节点也将不可用。',
                  onOk: () => deleteMutation.mutate(),
                })
              }
            >
              删除
            </Button>
          )}
        </Space>
      </Form>
    </div>
  );
}
