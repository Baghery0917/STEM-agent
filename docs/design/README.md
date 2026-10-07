# 前端设计 Demo

本目录存放纯静态 HTML demo，不依赖后端，可直接在浏览器打开。

| 文件 | 说明 | 在线预览 |
|------|------|----------|
| `preview/` | **真实前端的静态构建**（feat/teaching-emotion-strategy 分支，内置假后端，所有交互可点） | [打开](https://raw.githack.com/Baghery0917/STEM-agent/design/agent-ui-demo/docs/design/preview/index.html) |
| `current-ui-demo.html` | 复刻 `feat/teaching-emotion-strategy` 分支当前前端（Ant Design 风格，三栏教学页、练习流程、报告页、摄像头小窗） | [打开](https://raw.githack.com/Baghery0917/STEM-agent/design/agent-ui-demo/docs/design/current-ui-demo.html) |
| `agent-ui-demo.html` | 对话式界面重设计方案 | [打开](https://raw.githack.com/Baghery0917/STEM-agent/design/agent-ui-demo/docs/design/agent-ui-demo.html) |

`current-ui-demo.html` 支持 hash 路由直达页面，例如：

- `#/login` 登录页
- `#/teaching/12?student=1` 教学会话（已生成完）
- `#/teaching/12?stage=running&student=1` 流水线生成中
- `#/teaching/12?stage=failed&student=1` 生成失败
- `#/practice/7?student=1` 答题中
- `#/practice/5?student=1` 练习回顾
- `#/report?student=1` 学习报告

`student=1` 参数跳过登录页直接选中学生。截图见 `current-*.png`。

## 真实前端预览（preview/）

由 `frontend` 目录用 `VITE_PREVIEW_MOCK=1 npx vite build --mode preview` 构建，浏览器内拦截 `/api/v1` 请求返回假数据，
教学流式回复、练习提交 / 跳过 / 星标、练习转教学、自评、报告、设置全部可操作，刷新后数据重置。

直达路由（hash）：

- `#/login` 选择学生；「教师 / 管理员」页签的预览口令是 `admin`
- `#/teaching` 新对话 · `#/teaching/12` 进行中的会话
- `#/practice/new` 练习参数 · `#/practice/7` 做题中（计时 · 统一批改） · `#/practice/5` 已完成的练习回顾
- 左栏搜索框试试「摩擦」；报告页点「让评价处点评」
- `#/report` 学习报告 · `#/settings` 设置

重新生成：

```bash
cd frontend && VITE_PREVIEW_MOCK=1 npx vite build --mode preview --outDir ../docs/design/preview --emptyOutDir
```
