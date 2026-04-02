# 多平台 AI 智能体 (Weibo & Tieba Auto-Post)

一个基于 Playwright + Streamlit + 通义千问大模型的自动化社交媒体助手。支持微博超话、百度贴吧的自动签到、热门/最新素材抓取及 AI 智能回帖。

## 功能特性
- **微博模块**：支持最新 50 条动态抓取，自动关注超话。
- **贴吧模块**：适配新版 Quill 编辑器，精准容器抓取，识别连签状态。
- **AI 大脑**：调用通义千问生成具备“网感”的玩家吐槽。

## 快速开始
1. **克隆项目**：`git clone `
2. **安装依赖**：`pip install -r requirements.txt`
3. **安装浏览器驱动**：`playwright install chromium`
4. **配置环境**：将 `.env.example` 改名为 `.env` 并填入 API Key。
5. **启动应用**：`streamlit run app.py`