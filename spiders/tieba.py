import os
import time

from streamlit import container
from playwright.sync_api import sync_playwright
from .base import BasePlatform

# 💡 辅助函数：百度系 Cookie 注入
def parse_tieba_cookie_string(cookie_str):
    cookies = []
    cookie_str = cookie_str.strip().strip('"').strip("'")
    for item in cookie_str.split(';'):
        if '=' in item:
            name, value = item.strip().split('=', 1)
            # 同时注入主域和子域，确保权限覆盖
            for domain in ['.baidu.com', 'tieba.baidu.com']:
                cookies.append({
                    'name': name, 
                    'value': value, 
                    'domain': domain, 
                    'path': '/'
                })
    return cookies

class TiebaPlatform(BasePlatform):
    
    def get_hot_topics(self):
        """
        精准抓取 feed-list-container 容器内的热门内容（优化超时版本）
        """
        print(f"🕸️ [贴吧引擎] 正在尝试进入页面...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', 
        '--disable-setuid-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled'])
            context = browser.new_context()
            context.add_cookies(parse_tieba_cookie_string(self.cookie_str))
            page = context.new_page()
            
            try:
                # 🚀 优化 1：将等待条件改为 domcontentloaded，避免被广告脚本拖死
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=45000)
                
                # 🚀 优化 2：显式等待核心容器出现，只要它出来了，哪怕背景图没加载完也行
                print("⏳ 等待 feed-list-container 渲染...")
                try:
                    page.wait_for_selector(".feed-list-container", timeout=10000)
                except:
                    print("⚠️ 容器加载超时，尝试直接解析当前页面...")

                # 模拟滚动，让更多数据流出
                for _ in range(3): 
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(1000)
                
                # 🚀 核心逻辑：锁定容器
                container = page.locator(".feed-list-container").first
                
                hot_topics = []
                # 针对新版贴吧的类名：thread-content 或带有 content-- 的 div
                # 也可以直接找文本，只要它在容器内
                items = container.locator(".thread-item, .thread-main, [class*='item--']").all()
                
                for item in items:
                    # 我们重点抓取标题（title）和内容摘要
                    content_piece = item.locator(".title, .thread-content, [class*='content--'], [class*='title--']").first
                    if content_piece.count() > 0:
                        text = content_piece.inner_text().strip()
                        if len(text) > 8: 
                            hot_topics.append(text)

                # 兜底：如果上面没抓到，抓取容器内所有长度合适的文本
                if not hot_topics:
                    print("⚠️ 精准提取失败，尝试全量文本提取...")
                    elements = container.locator("div, span").all()
                    hot_topics = [el.inner_text().strip() for el in elements if 15 < len(el.inner_text().strip()) < 200]

                # 最终结果去重
                hot_topics = list(dict.fromkeys(hot_topics))
                
                result = "\n".join(hot_topics[:50])
                if result:
                    print(f"✅ 成功提取到 {len(hot_topics[:50])} 条素材")
                else:
                    print("❌ 容器内未发现有效文本内容")
                return result
                
            except Exception as e:
                print(f"❌ 贴吧访问异常: {e}")
                # 如果是超时导致的，尝试返回当前已经加载出来的部分内容
                return ""
            finally:
                context.close()
    def auto_checkin(self):
        """自动签到（兼容：签到、已签到、连签n天）"""
        print(f"📍 [贴吧引擎] 正在执行签到检查...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', 
        '--disable-setuid-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled'])
            context = browser.new_context()
            context.add_cookies(parse_tieba_cookie_string(self.cookie_str))
            page = context.new_page()

            try:
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)

                # 🚀 修复点 1：使用更兼容的文本定位方式检查“已签到”状态
                # 这种写法不会触发 CSS 解析错误
                is_signed_in = page.get_by_text("已签到").first.is_visible() or \
                               page.get_by_text("连签").first.is_visible()
                
                if is_signed_in:
                    return True, "今天已经签到过啦！（检测到：已签到/连签）"
                
                # 🚀 修复点 2：拆分选择器，使用 or 逻辑寻找按钮
                # 先找精准类名，找不到再找带“签到”文字的按钮
                sign_btn = page.locator("div.follow-sign").first
                if sign_btn.count() == 0:
                    sign_btn = page.get_by_text("签到", exact=True).first

                if sign_btn.count() > 0 and sign_btn.is_visible():
                    print("🎯 找到贴吧签到按钮，正在点击...")
                    sign_btn.click()
                    page.wait_for_timeout(3000)
                    return True, "🎉 贴吧签到动作已触发！"
                else:
                    return False, "❌ 未能锁定签到按钮，请确认是否已关注该吧。"
            except Exception as e:
                return False, f"贴吧签到异常: {e}"
            finally:
                context.close()

    def publish_post(self, text_to_publish):
        """精准适配新版 Quill 编辑器与遮罩发布按钮"""
        print(f"🦾 [贴吧引擎] 正在精准执行发帖流程...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', 
        '--disable-setuid-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled'])
            context = browser.new_context()
            context.add_cookies(parse_tieba_cookie_string(self.cookie_str))
            page = context.new_page()

            try:
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

                # 1. 触发发帖窗口 (兼容新旧版)
                trigger = page.locator(".button-wrapper--add-post, .add-btn, button:has-text('发贴'), i.icon-post").first
                if trigger.count() > 0:
                    trigger.click()
                    page.wait_for_timeout(2000)

                # 2. 填写【标题】 - 基于 ID tb-editor-title (针对 p1)
                title_editor = page.locator("#tb-editor-title .ql-editor").first
                if title_editor.count() > 0:
                    # 贴吧要求 5-31 字，AI 文案太短则补全
                    title_text = text_to_publish[:25]
                    if len(title_text) < 5: title_text = f"关于【{title_text}】的碎碎念"
                    
                    # Quill 编辑器必须用 Type，不能用 fill
                    title_editor.click()
                    page.wait_for_timeout(500)
                    page.keyboard.type(title_text, delay=30) 
                    print(f"✍️ 标题已填入")

                # 3. 填写【正文】 - 基于 ID tb-editor-content (针对 p2)
                content_editor = page.locator("#tb-editor-content .ql-editor").first
                if content_editor.count() > 0:
                    content_editor.click()
                    page.wait_for_timeout(500)
                    
                    # 清除默认空行
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    
                    # 模拟打字输入正文
                    page.keyboard.type(text_to_publish, delay=10)
                    print("✍️ 正文已填入")
                    page.wait_for_timeout(2000)

                    # 4. 点击【发布】提交按钮 (针对 p5 + 解决遮罩拦截)
                    # 🚀 策略：使用 dispatch_event("click") 强制底层触发，无视任何遮罩层
                    # 选择器使用了你提供的精准 Primary 类名
                    submit_btn = page.locator(".issue-btn.button-wrapper--primary, button:has-text('发布')").first
                    
                    if submit_btn.count() > 0:
                        print("🚀 正在通过 JS 强制穿透遮罩点击发布...")
                        
                        # 在点击发布前，模拟按一下 Tab 键，确保编辑器失去焦点并保存内容
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(1000)

                        # 使用原生的 click 事件，穿透隐形遮罩层
                        submit_btn.dispatch_event("click")
                        
                        print("✅ [贴吧引擎] 发布指令已发出，任务达成！")
                        page.wait_for_timeout(5000) # 等待跳转或成功提示
                    else:
                        print("❌ 未能锁定 Primary 发布按钮，请检查类名")
                
            except Exception as e:
                print(f"❌ 贴吧发帖异常: {e}")
            finally:
                context.close()