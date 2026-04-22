import { useMutation } from '@tanstack/react-query';
import {
  App,
  Button,
  Card,
  Checkbox,
  Divider,
  Form,
  InputNumber,
  Radio,
  Space,
  Tag,
  TreeSelect,
  Typography,
} from 'antd';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startFocused, startGeneral } from '@/api/practice';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import { useStudentStore } from '@/stores/studentStore';
import type { Difficulty, PracticeMode } from '@/api/types';
import { DIFFICULTY_OPTIONS, PRACTICE_MODE_LABEL } from '@/utils/enums';

interface FormValues {
  knowledge_point_ids: number[];
  difficulty_range: Difficulty[];
  mode: PracticeMode;
  total_count?: number;
}

export default function PracticeSetup() {
  const student = useStudentStore((s) => s.current);
  const navigate = useNavigate();
  const { message } = App.useApp();
  const tree = useKnowledgeTree();
  const [form] = Form.useForm<FormValues>();
  const mode = Form.useWatch('mode', form) ?? 'focused';

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
          key: s.id,
        })),
      })),
    }));
  }, [tree.data]);

  const focusedMutation = useMutation({
    mutationFn: startFocused,
    onSuccess: (data) => navigate(`/practice/${data.session.id}`, { state: data }),
    onError: (err: Error) => message.error(err.message),
  });

  const generalMutation = useMutation({
    mutationFn: startGeneral,
    onSuccess: (data) => navigate(`/practice/${data.session.id}`, { state: data }),
    onError: (err: Error) => message.error(err.message),
  });

  const handleSubmit = (values: FormValues) => {
    if (!student) return;
    const payload = {
      student_id: student.id,
      knowledge_point_ids: values.knowledge_point_ids,
      difficulty_range: values.difficulty_range,
    };
    if (values.mode === 'focused') {
      focusedMutation.mutate({ ...payload, total_count: values.total_count ?? 10 });
    } else {
      generalMutation.mutate(payload);
    }
  };

  if (!student) return null;

  return (
    <div className="page-container" style={{ maxWidth: 820 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 8,
        }}
      >
        <Typography.Title level={3} style={{ margin: 0 }}>
          开始练习
        </Typography.Title>
        <Button onClick={() => navigate('/practice/history')}>查看历史记录</Button>
      </div>
      <Typography.Paragraph type="secondary">
        选择知识点、难度与练习模式，系统将从题库检索符合条件的题目。
      </Typography.Paragraph>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            knowledge_point_ids: [],
            difficulty_range: ['easy', 'medium'],
            mode: 'focused',
            total_count: 10,
          }}
        >
          <Form.Item
            label="知识点（节）"
            name="knowledge_point_ids"
            rules={[{ required: true, message: '请选择至少一个知识点' }]}
          >
            <TreeSelect
              multiple
              treeCheckable
              showCheckedStrategy="SHOW_CHILD"
              treeData={treeData}
              placeholder="请选择要练习的节"
              treeDefaultExpandAll
              loading={tree.isLoading}
              style={{ width: '100%' }}
              maxTagCount={8}
            />
          </Form.Item>

          <Form.Item
            label="难度范围"
            name="difficulty_range"
            rules={[{ required: true, message: '请选择至少一个难度' }]}
          >
            <Checkbox.Group options={DIFFICULTY_OPTIONS} />
          </Form.Item>

          <Form.Item label="练习模式" name="mode" rules={[{ required: true }]}>
            <Radio.Group>
              <Radio value="focused">{PRACTICE_MODE_LABEL.focused}</Radio>
              <Radio value="general">{PRACTICE_MODE_LABEL.general}</Radio>
            </Radio.Group>
          </Form.Item>

          {mode === 'focused' && (
            <Form.Item
              label="题目数量（1-100，题库不足时按实际返回）"
              name="total_count"
              rules={[{ required: true, message: '请输入数量' }]}
            >
              <InputNumber min={1} max={100} style={{ width: 200 }} />
            </Form.Item>
          )}

          <Divider />
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={focusedMutation.isPending || generalMutation.isPending}
            >
              开始练习
            </Button>
            <Tag color="blue">Focused：批量抽题必答</Tag>
            <Tag color="geekblue">General：每题单抽，可跳过</Tag>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
