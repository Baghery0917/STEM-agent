import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, HashRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App as AntdApp, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';

import App from './App';
import { apiClient } from './api/client';
import './styles/global.css';
import 'katex/dist/katex.min.css';

// 预览构建（VITE_PREVIEW_MOCK=1）：浏览器内假后端 + hash 路由，可作为纯静态文件托管
const PREVIEW = import.meta.env.VITE_PREVIEW_MOCK === '1';
if (PREVIEW) {
  const { installPreviewMock } = await import('./mock/previewMock');
  installPreviewMock('/api/v1');
  apiClient.defaults.baseURL = '/api/v1';
  apiClient.defaults.adapter = 'fetch';
}
const Router = PREVIEW ? HashRouter : BrowserRouter;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#3b5bdb',
          borderRadius: 6,
        },
      }}
    >
      <QueryClientProvider client={queryClient}>
        <AntdApp>
          <Router>
            <App />
          </Router>
        </AntdApp>
      </QueryClientProvider>
    </ConfigProvider>
  </React.StrictMode>,
);
