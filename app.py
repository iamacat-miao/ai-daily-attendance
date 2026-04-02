import sys
import asyncio

# 🚨 终极补丁：解决 Windows 下 Streamlit 和 Playwright 的异步循环冲突
# 这段代码必须放在所有的 import 最前面！
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import json

# 引入我们刚才重构的各大平台专属类
from spiders.weibo import WeiboPlatform
from spiders.tieba import TiebaPlatform
# 引入 AI 大脑（请确保 main.py 中包含此函数）
from weibo_ai import get_ai_gamer_comment 
import os
import subprocess
import streamlit as st

# --- 🚀 针对 Python 3.14 + Streamlit Cloud 的内核修复 ---
@st.cache_resource
def ensure_playwright_browsers():
    # 1. 强制设定浏览器下载路径到用户的家目录缓存，避开 venv 权限问题
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/adminuser/.cache/ms-playwright"
    
    # 获取当前 Python 解释器的路径，确保在同一个 venv 里操作
    python_exe = os.sys.executable
    
    try:
        # 检查内核是否已存在
        if not os.path.exists(os.environ["PLAYWRIGHT_BROWSERS_PATH"]):
            with st.spinner("首次部署：正在为 Python 3.14 下载专用浏览器内核..."):
                # 💡 关键：安装 chromium 及其最新的 headless-shell
                subprocess.run([python_exe, "-m", "playwright", "install", "chromium", "--with-deps"], check=True)
            st.success("✅ 浏览器环境已成功初始化")
        else:
            print("🚀 环境检测正常")
    except Exception as e:
        st.error(f"❌ 内核安装失败: {e}")
        # 最后的兜底尝试
        os.system(f"{python_exe} -m playwright install chromium")

# 必须在所有逻辑开始前运行
ensure_playwright_browsers()
st.set_page_config(page_title="多平台 AI 智能体", page_icon="🤖", layout="centered")

st.title("🤖 多平台全自动 AI 智能体")
st.markdown("支持多平台的 **自动签到 $\\rightarrow$ 抓取舆情 $\\rightarrow$ AI 分析 $\\rightarrow$ 自动拟人跟帖**。")

st.divider()

# ================= 动态路由与参数配置 =================
platform_choice = st.selectbox("🎯 选择目标平台", ["微博超话", "百度贴吧"])

# 根据用户的选择，动态改变 UI 输入框的内容，并决定使用哪个底座引擎
if platform_choice == "微博超话":
    # 📝 微博默认超话配置字典
    weibo_options = {
        "王者荣耀": "https://weibo.com/p/100808ccb61d96c8f867d4f6c412e95c4f173a/super_index",
        "英雄联盟": "https://weibo.com/p/1008082531e21b0e0d5a353683f2a3dc26e0be/super_index",
        "原神": "https://weibo.com/p/10080877963953556555436666874/super_index",
        "自定义输入": ""
    }
    
    selected_community = st.selectbox("🗂️ 选择超话板块", list(weibo_options.keys()))
    
    # 如果选了“自定义输入”，才显示输入框；否则直接使用字典里配好的 URL
    if selected_community == "自定义输入":
        target_url = st.text_input("🔗 请输入微博超话完整 URL")
    else:
        target_url = weibo_options[selected_community]
        
    user_cookie = st.text_input("🔑 微博 Cookie (必须包含 SUB=...)", type="password")
    PlatformEngine = WeiboPlatform 

else:
    # 📝 贴吧默认社区配置字典
    tieba_options = {
        "王者荣耀": "https://tieba.baidu.com/f?kw=%E7%8E%8B%E8%80%85%E8%8D%A3%E8%80%80",
        "抗压背锅": "https://tieba.baidu.com/f?kw=%E6%8A%97%E5%8E%8B%E8%83%8C%E9%94%85",
        "显卡": "https://tieba.baidu.com/f?kw=%E6%98%BE%E5%8D%A1",
        "自定义输入": ""
    }
    
    selected_community = st.selectbox("🗂️ 选择贴吧板块", list(tieba_options.keys()))
    
    if selected_community == "自定义输入":
        target_url = st.text_input("🔗 请输入贴吧完整 URL")
    else:
        target_url = tieba_options[selected_community]
        
    user_cookie = st.text_input("🔑 贴吧 Cookie (必须包含 BDUSS=...)", type="password")
    PlatformEngine = TiebaPlatform

# 签到开关
need_checkin = st.checkbox("☑️ 顺手帮我完成当前板块的【自动签到】", value=True)

st.divider()

# ================= 核心执行工作流 =================
if st.button("🚀 开始一键执行", use_container_width=True, type="primary"):
    
    if not target_url or not user_cookie:
        st.error("❌ 请先输入有效的 URL 和 Cookie！")
    else:
        # 🌟 架构高光时刻：实例化选中的平台引擎
        # 不管是微博还是贴吧，它们都继承自 BasePlatform，拥有相同的方法名
        engine = PlatformEngine(target_url, user_cookie)
        
        # ---------------- 阶段 0：执行自动签到 ----------------
        if need_checkin:
            with st.spinner(f"📍 正在帮您执行 {platform_choice} 签到..."):
                success, msg = engine.auto_checkin()
                if success:
                    st.success(msg)
                else:
                    st.warning(msg)

        # ---------------- 阶段 1：抓取素材 ----------------
        with st.spinner(f"🕷️ 机械眼正在潜入 {platform_choice} 疯狂抓取数据..."):
            hot_topics = engine.get_hot_topics()
            
        if not hot_topics:
            st.error("⚠️ 没抓到帖子，流程终止。可能是 Cookie 过期、URL 错误或风控拦截。")
        else:
            st.success(f"✅ 成功抓取素材！")
            with st.expander("点击查看抓取到的原始素材文本", expanded=False):
                st.text(hot_topics)

            # ---------------- 阶段 2：AI 思考 ----------------
            with st.spinner("🧠 通义千问大模型正在深度分析并构思网感文案..."):
                ai_result_str = get_ai_gamer_comment(hot_topics)
                
                # 清洗大模型的 Markdown 外壳（照妖镜保护层）
                clean_str = ai_result_str.strip()
                if clean_str.startswith("```json"):
                    clean_str = clean_str[7:]
                elif clean_str.startswith("```"):
                    clean_str = clean_str[3:]
                if clean_str.endswith("```"):
                    clean_str = clean_str[:-3]
                clean_str = clean_str.strip()

                try:
                    # 尝试解析纯净的 JSON
                    ai_data = json.loads(clean_str)
                    post_text = ai_data.get("content", "")
                    
                    st.info(f"**📝 AI 最终生成文案：**\n\n{post_text}")
                    
                    # ---------------- 阶段 3：执行发送 ----------------
                    if post_text:
                        with st.spinner("🦾 机械臂正在接管浏览器，准备发帖..."):
                            engine.publish_post(post_text)
                            
                        st.balloons()
                        st.success("🎉 全套动作执行完毕！请去弹出的无头浏览器中（或直接去原网页）确认结果！")
                        
                except Exception as e:
                    st.error(f"❌ JSON 解析失败的具体原因: {e}")
                    st.warning("👇 下面是大模型返回的原始字符串，请检查 Prompt 是否严谨：")
                    st.code(ai_result_str, language="text")