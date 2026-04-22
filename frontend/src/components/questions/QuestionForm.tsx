import { App, Form, Input, InputNumber, Modal, Select, TreeSelect } from 'antd';
import { useEffect, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createQuestion, updateQuestion } from '@/api/questions';
import type {
  Difficulty,
  QuestionCreate,
  QuestionResponse,
  QuestionType,
} from '@/api/types';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import { DIFFICULTY_OPTIONS, QUESTION_TYPE_OPTIONS } from '@/utils/enums';

interface Props {
  open: boolean;
  onClose: () => void;
  initial?: QuestionResponse | null;
}

export default function QuestionForm({ open, onClose, initial }: Props) {
  const [form] = Form.useForm<QuestionCreate>();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const tree = useKnowledgeTree();

  const treeData = useMemo(() => {
    if (!tree.data) return [];
    return tree.data.volumes.map((v) => ({
      title: v.title,
      value: `v-${v.id}`,
      selectable: false,
      children: (tree.data!.byVolume.get(v.id) ?? []).map((c) => ({
        title: c.title,
        value: `c-${c.id}`,
        selectable: false,
        children: (tree.data!.byChapter.get(c.id) ?? []).map((s) => ({
          title: s.title,
          value: s.id,
        })),
      })),
    }));
  }, [tree.data]);

  useEffect(() => {
    if (!open) return;
    if (initial) {
      form.setFieldsValue({
        type: initial.type,
        content: initial.content,
        content_image: initial.content_image ?? '',
        answer: initial.answer,
        answer_image: initial.answer_image ?? '',
        analysis: initial.analysis ?? '',
        analysis_image: initial.analysis_image ?? '',
        difficulty: initial.difficulty,
        knowledge_point_ids: initial.knowledge_point_ids,
      });
    } else {
      form.resetFields();
      form.setFieldsValue({
        type: 'single_choice' as QuestionType,
        difficulty: 'medium' as Difficulty,
        knowledge_point_ids: [],
      });
    }
  }, [open, initial, form]);

  const mutation = useMutation({
    mutationFn: async (values: QuestionCreate) => {
      if (initial) return updateQuestion(initial.id, values);
      return createQuestion(values);
    },
    onSuccess: () => {
      message.success(initial ? '已更新' : '已创建');
      queryClient.invalidateQueries({ queryKey: ['questions'] });
      onClose();
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Modal
      open={open}
      title={initial ? '编辑题目' : '新建题目'}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={mutation.isPending}
      width={720}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)}>
        <Form.Item label="题目类型" name="type" rules={[{ required: true }]}>
          <Select options={QUESTION_TYPE_OPTIONS} />
        </Form.Item>
        <Form.Item
          label="题目内容"
          name="content"
          rules={[{ required: true, message: '请输入题目内容' }]}
        >
          <Input.TextArea
            autoSize={{ minRows: 4, maxRows: 12 }}
            placeholder="选择题可在正文下方换行写 A./B./C./D. 选项"
          />
        </Form.Item>
        <Form.Item label="题目图片 URL（可选）" name="content_image">
          <Input placeholder="https://..." />
        </Form.Item>
        <Form.Item
          label="答案"
          name="answer"
          rules={[{ required: true, message: '请输入答案' }]}
        >
          <Input placeholder="如 A / AB / 9.8" />
        </Form.Item>
        <Form.Item label="答案图片 URL（可选）" name="answer_image">
          <Input placeholder="https://..." />
        </Form.Item>
        <Form.Item label="答案解析" name="analysis">
          <Input.TextArea autoSize={{ minRows: 3, maxRows: 8 }} />
        </Form.Item>
        <Form.Item label="解析图片 URL（可选）" name="analysis_image">
          <Input placeholder="https://..." />
        </Form.Item>
        <Form.Item label="难度" name="difficulty" rules={[{ required: true }]}>
          <Select options={DIFFICULTY_OPTIONS} />
        </Form.Item>
        <Form.Item
          label="关联知识点（节）"
          name="knowledge_point_ids"
          extra="可多选，节级别"
        >
          <TreeSelect
            multiple
            treeCheckable
            showCheckedStrategy="SHOW_CHILD"
            treeData={treeData}
            treeDefaultExpandAll
            placeholder="选择关联的节"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
