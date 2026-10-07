import { Button, Layout, Menu, Typography } from 'antd';
import {
  ApartmentOutlined,
  ArrowLeftOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  NotificationOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { clearAdminToken, getAdminToken } from '@/api/admin';

const { Header, Sider, Content } = Layout;

const MENU = [
  { key: '/admin/knowledge', label: '知识结构', icon: <ApartmentOutlined /> },
  { key: '/admin/questions', label: '题库管理', icon: <FileTextOutlined /> },
  { key: '/admin/students', label: '学生管理', icon: <TeamOutlined /> },
  { key: '/admin/news', label: '物理新闻', icon: <NotificationOutlined /> },
  { key: '/admin/db', label: '数据库浏览', icon: <DatabaseOutlined /> },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const activeKey =
    MENU.find((m) => location.pathname.startsWith(m.key))?.key ?? '/admin/knowledge';
  const token = getAdminToken();

  // 未登录管理员：回到登录页的管理员入口
  useEffect(() => {
    if (!token) navigate('/login?admin=1', { replace: true });
  }, [token, navigate]);

  if (!token) return null;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#1f2937',
          padding: '0 24px',
          gap: 16,
        }}
      >
        <Typography.Title level={4} style={{ margin: 0, color: '#fff' }}>
          STEM 管理台
        </Typography.Title>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          style={{ color: '#fff', marginLeft: 'auto' }}
          onClick={() => { clearAdminToken(); navigate('/login', { replace: true }); }}
        >
          退出管理台
        </Button>
      </Header>
      <Layout>
        <Sider theme="light" width={220}>
          <Menu
            mode="inline"
            items={MENU}
            selectedKeys={[activeKey]}
            onClick={(info) => navigate(info.key)}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Content style={{ padding: 24, background: '#f5f7fb' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
