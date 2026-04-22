import { Avatar, Dropdown, Layout, Menu, Typography } from 'antd';
import {
  BookOutlined,
  CommentOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  LineChartOutlined,
  LogoutOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useRequireStudent } from '@/hooks/useRequireStudent';
import { useStudentStore } from '@/stores/studentStore';

const { Header, Content } = Layout;

const MENU = [
  { key: '/home', label: '首页', icon: <DashboardOutlined /> },
  { key: '/teaching', label: '教学对话', icon: <CommentOutlined /> },
  { key: '/practice/setup', label: '练习', icon: <ExperimentOutlined /> },
  { key: '/report', label: '学习报告', icon: <LineChartOutlined /> },
];

export default function StudentLayout() {
  const student = useRequireStudent();
  const navigate = useNavigate();
  const location = useLocation();
  const setCurrent = useStudentStore((s) => s.setCurrent);

  if (!student) return null;

  const activeKey =
    MENU.find((m) => location.pathname === m.key || location.pathname.startsWith(m.key + '/'))
      ?.key ?? '/home';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#fff',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          padding: '0 24px',
          gap: 24,
        }}
      >
        <Typography.Title level={4} style={{ margin: 0, color: '#2563eb' }}>
          <BookOutlined style={{ marginRight: 8 }} />
          STEM 智能教学
        </Typography.Title>
        <Menu
          mode="horizontal"
          items={MENU}
          selectedKeys={[activeKey]}
          onClick={(info) => navigate(info.key)}
          style={{ flex: 1, borderBottom: 'none' }}
        />
        <Dropdown
          menu={{
            items: [
              {
                key: 'admin',
                icon: <SettingOutlined />,
                label: '管理台',
                onClick: () => navigate('/admin/knowledge'),
              },
              { type: 'divider' },
              {
                key: 'logout',
                icon: <LogoutOutlined />,
                label: '切换学生',
                onClick: () => {
                  setCurrent(null);
                  navigate('/login');
                },
              },
            ],
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <Avatar icon={<UserOutlined />} />
            <span>{student.name}</span>
          </span>
        </Dropdown>
      </Header>
      <Content>
        <Outlet />
      </Content>
    </Layout>
  );
}
