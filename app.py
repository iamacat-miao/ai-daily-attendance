import asyncio
import json
import os
import subprocess
import sys

import streamlit as st

from spiders.playwright_env import configure_playwright_browser_path
from spiders.tieba import TiebaPlatform
from spiders.weibo import WeiboPlatform
from weibo_ai import get_ai_gamer_comment


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@st.cache_resource
def ensure_playwright_browsers():
    browser_dir = configure_playwright_browser_path()
    python_exe = sys.executable

    if any(os.scandir(browser_dir)):
        return browser_dir

    with st.spinner("首次启动，正在安装 Playwright Chromium 浏览器..."):
        subprocess.run([python_exe, "-m", "playwright", "install", "chromium"], check=True)

    return browser_dir


def clean_json_block(text):
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    return clean_text.strip()


ensure_playwright_browsers()

st.set_page_config(page_title="多平台 AI 智能体", page_icon="🤖", layout="centered")
st.title("🤖 多平台全自动 AI 智能体")
st.markdown("支持微博超话、百度贴吧的自动签到、内容抓取、AI 生成和自动发帖。")

st.divider()

platform_choice = st.selectbox("选择目标平台", ["微博超话", "百度贴吧"])

if platform_choice == "微博超话":
    options = {
        "王者荣耀": "https://weibo.com/p/100808ccb61d96c8f867d4f6c412e95c4f173a/super_index",
        "英雄联盟": "https://weibo.com/p/1008082531e21b0e0d5a353683f2a3dc26e0be/super_index",
        "原神": "https://weibo.com/p/10080877963953556555436666874/super_index",
        "自定义输入": "",
    }
    selected_community = st.selectbox("选择超话板块", list(options.keys()))
    if selected_community == "自定义输入":
        target_url = st.text_input("请输入微博超话完整 URL")
    else:
        target_url = options[selected_community]
    user_cookie = st.text_input("微博 Cookie（必须包含 SUB=...）", type="password")
    platform_engine = WeiboPlatform
else:
    options = {
        "王者荣耀": "https://tieba.baidu.com/f?kw=%E7%8E%8B%E8%80%85%E8%8D%A3%E8%80%80",
        "抗压背锅": "https://tieba.baidu.com/f?kw=%E6%8A%97%E5%8E%8B%E8%83%8C%E9%94%85",
        "显卡": "https://tieba.baidu.com/f?kw=%E6%98%BE%E5%8D%A1",
        "自定义输入": "",
    }
    selected_community = st.selectbox("选择贴吧板块", list(options.keys()))
    if selected_community == "自定义输入":
        target_url = st.text_input("请输入贴吧完整 URL")
    else:
        target_url = options[selected_community]
    user_cookie = st.text_input("贴吧 Cookie（必须包含 BDUSS=...）", type="password")
    platform_engine = TiebaPlatform

need_checkin = st.checkbox("执行自动签到", value=True)

st.divider()

if st.button("开始一键执行", use_container_width=True, type="primary"):
    if not target_url or not user_cookie:
        st.error("请先输入有效的 URL 和 Cookie。")
    else:
        engine = platform_engine(target_url, user_cookie)

        if need_checkin:
            with st.spinner(f"正在执行 {platform_choice} 签到..."):
                success, message = engine.auto_checkin()
            if success:
                st.success(message)
            else:
                st.warning(message)

        with st.spinner(f"正在抓取 {platform_choice} 的内容..."):
            hot_topics = engine.get_hot_topics()

        if not hot_topics:
            st.error("未抓取到有效内容。可能是 Cookie 过期、URL 错误或页面风控。")
        else:
            st.success("内容抓取成功。")
            with st.expander("查看抓取到的原始内容", expanded=False):
                st.text(hot_topics)

            with st.spinner("AI 正在生成文案..."):
                ai_result_str = get_ai_gamer_comment(hot_topics)

            try:
                ai_data = json.loads(clean_json_block(ai_result_str))
                post_text = ai_data.get("content", "").strip()
                st.info(f"**AI 生成文案：**\n\n{post_text}")

                if post_text:
                    with st.spinner("正在执行自动发帖..."):
                        engine.publish_post(post_text)
                    st.balloons()
                    st.success("流程已执行完成，请到目标页面确认结果。")
                else:
                    st.warning("AI 返回成功，但没有生成可发布的 content。")
            except Exception as exc:
                st.error(f"AI 返回结果不是合法 JSON：{exc}")
                st.code(ai_result_str, language="text")
