# 前端设计 Demo

本目录存放纯静态 HTML demo，不依赖后端，可直接在浏览器打开。

| 文件 | 说明 | 在线预览 |
|------|------|----------|
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
