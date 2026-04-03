# spiders/weibo.py
from .base import BasePlatform
from .playwright_env import configure_playwright_browser_path
from playwright.sync_api import sync_playwright

# 辅助函数可以放在类外面
def parse_cookie_string(cookie_str):
    cookies = []
    for item in cookie_str.split(';'):
        if '=' in item:
            name, value = item.strip().split('=', 1)
            cookies.append({'name': name, 'value': value, 'domain': '.weibo.com', 'path': '/'})
    return cookies

class WeiboPlatform(BasePlatform):
    def get_hot_topics(self):
            print(f"🕸️ [微博引擎] 启动无头浏览器...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', 
        '--disable-setuid-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled'])
                context = browser.new_context()
                context.add_cookies(parse_cookie_string(self.cookie_str))
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                try:
                    page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)

                    # =======================================================
                    # 🚀 目标切换：寻找并点击“最新”时间线
                    # =======================================================
                    print("🔍 [微博引擎] 寻找并切换到【最新】板块...")
                    # 超话的最新页面标签通常是“最新”或“实时”
                    latest_tab = page.locator("a:has-text('最新'), li:has-text('最新'), span:has-text('最新'), a:has-text('实时')").first
                    if latest_tab.count() > 0 and latest_tab.is_visible():
                        latest_tab.click()
                        page.wait_for_timeout(4000) 
                    else:
                        print("⚠️ 未找到明显的【最新】标签，将抓取默认时间线。")

                    # =======================================================
                    # 🚀 深度增加：加大鼠标滚动次数以刷出至少 50 条
                    # =======================================================
                    print("📜 [微博引擎] 正在加大马力滚动加载，目标：50条...")
                    for _ in range(12):  # 滚动次数从 6 增加到 12
                        page.mouse.wheel(0, 3000)
                        page.wait_for_timeout(1500)
                    
                    selectors = ['div[class*="detail_wbtext"]', 'div[class*="wbpro-text"]', 'div[class*="WB_text"]', 'div[dir="auto"]']
                    hot_topics = []
                    for sel in selectors:
                        elements = page.query_selector_all(sel)
                        valid_texts = [el.inner_text().strip() for el in elements if len(el.inner_text().strip()) > 10]
                        # 判断当前选择器是否有效（抓到了足够多的数据才算对）
                        if len(valid_texts) > 20: 
                            hot_topics = valid_texts
                            break

                    # =======================================================
                    # 🚀 容量放宽：截取前 50 条
                    # =======================================================
                    result_text = "\n".join(hot_topics[:50])
                    print(f"✅ 成功抓取到 {len(hot_topics[:50])} 条最新动态")
                    return result_text
                    
                except Exception as e:
                    print(f"❌ 抓取失败: {e}")
                    return ""
                finally:
                    context.close()
    def auto_checkin(self):
        print(f"📍 [微博引擎] 执行超话签到...")
        configure_playwright_browser_path()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', 
        '--disable-setuid-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled'])
            context = browser.new_context()
            
            try:
                context.add_cookies(parse_cookie_string(self.cookie_str))
            except Exception as e:
                return False, f"Cookie 解析失败: {e}"

            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)

                if page.locator("text='已签到'").count() > 0:
                    return True, "今天已经签到过啦，无需重复签到！"
                
                sign_btn = page.locator("text='签到'").first
                if sign_btn.count() > 0:
                    sign_btn.click()
                    page.wait_for_timeout(3000)
                    return True, "✅ 签到动作已触发"
                else:
                    return False, "❌ 未找到签到按钮"
            except Exception as e:
                return False, f"签到异常: {e}"
            finally:
                context.close()

    def publish_post(self, text_to_publish):
        print(f"🦾 [微博引擎] 准备发帖...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', 
        '--disable-setuid-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled'])
            context = browser.new_context()
            context.add_cookies(parse_cookie_string(self.cookie_str))
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)

            try:
                print("🔍 检查是否已关注...")
                join_btn = page.locator('a[action-type="follow"], a:has-text("加关注")').first
                if join_btn.count() > 0 and join_btn.is_visible():
                    join_btn.click()
                    page.wait_for_timeout(3000) 
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(1000)
                
                input_box = page.locator("textarea[title='微博输入框'], textarea.W_input, textarea[placeholder*='有什么想和大家分享的']").first
                if input_box.count() > 0:
                    input_box.click()
                    input_box.fill(text_to_publish)
                    page.wait_for_timeout(3000)
                    
                    # 发送逻辑
                    send_btn = page.locator("a[title='发布'], a.W_btn_a, button:has-text('发布')").first
                    send_btn.click()
                    print("🚀 [微博引擎] 已经点击发送！")
                else:
                    print("❌ 未能锁定输入框")
            finally:
                context.close()
