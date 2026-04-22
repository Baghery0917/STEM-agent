import { useMutation, useQuery } from '@tanstack/react-query';
import {
  App,
  Avatar,
  Button,
  Card,
  Divider,
  Form,
  Input,
  List,
  Radio,
  Space,
  Spin,
  Typography,
} from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { createStudent, listStudents } from '@/api/students';
import type { Gender, StudentResponse } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { GENDER_LABEL } from '@/utils/enums';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const setCurrent = useStudentStore((s) => s.setCurrent);

  const studentsQuery = useQuery({
    queryKey: ['students', 'login'],
    queryFn: () => listStudents({ limit: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: (body: { name: string; gender: Gender }) => createStudent(body),
    onSuccess: (student) => {
      message.success(`已创建学生 ${student.name}`);
      handleSelect(student);
    },
    onError: (err: Error) => message.error(err.message),
  });

  const handleSelect = (student: StudentResponse) => {
    setCurrent(student);
    navigate('/home', { replace: true });
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #eef2ff 0%, #dbeafe 100%)',
        padding: 24,
      }}
    >
      <Card style={{ width: 520, boxShadow: '0 8px 32px rgba(30, 64, 175, 0.1)' }}>
        <Typography.Title level={3} style={{ textAlign: 'center', marginBottom: 8 }}>
          STEM 智能教学系统
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ textAlign: 'center' }}>
          选择或创建一个学生以进入系统
        </Typography.Paragraph>

        <Divider>已有学生</Divider>
        {studentsQuery.isLoading ? (
          <div style={{ textAlign: 'center', padding: 32 }}>
            <Spin />
          </div>
        ) : (studentsQuery.data?.length ?? 0) === 0 ? (
          <Typography.Text type="secondary">暂无学生，请先创建</Typography.Text>
        ) : (
          <List
            dataSource={studentsQuery.data}
            renderItem={(s) => (
              <List.Item
                actions={[
                  <Button type="primary" key="pick" onClick={() => handleSelect(s)}>
                    选择
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={<Avatar icon={<UserOutlined />} />}
                  title={s.name}
                  description={`ID: ${s.id} · ${GENDER_LABEL[s.gender]}`}
                />
              </List.Item>
            )}
          />
        )}

        <Divider>创建新学生</Divider>
        <Form
          layout="vertical"
          onFinish={(values) => createMutation.mutate(values)}
          initialValues={{ gender: 'male' }}
        >
          <Form.Item
            label="姓名"
            name="name"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" maxLength={100} />
          </Form.Item>
          <Form.Item label="性别" name="gender" rules={[{ required: true }]}>
            <Radio.Group>
              <Radio value="male">男</Radio>
              <Radio value="female">女</Radio>
              <Radio value="other">其他</Radio>
            </Radio.Group>
          </Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
              创建并进入
            </Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
