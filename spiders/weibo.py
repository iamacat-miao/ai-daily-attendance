from playwright.sync_api import sync_playwright

from .base import BasePlatform
from .playwright_env import launch_chromium


def parse_cookie_string(cookie_str):
    cookies = []
    for item in cookie_str.split(";"):
        if "=" in item:
            name, value = item.strip().split("=", 1)
            cookies.append(
                {"name": name, "value": value, "domain": ".weibo.com", "path": "/"}
            )
    return cookies


class WeiboPlatform(BasePlatform):
    def get_hot_topics(self):
        print("[weibo] start scraping")
        with sync_playwright() as p:
            browser = launch_chromium(p)
            context = browser.new_context()
            try:
                context.add_cookies(parse_cookie_string(self.cookie_str))
                page = context.new_page()
                page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)

                latest_tab = page.locator(
                    "a:has-text('最新'), li:has-text('最新'), span:has-text('最新'), a:has-text('实时')"
                ).first
                if latest_tab.count() > 0 and latest_tab.is_visible():
                    latest_tab.click()
                    page.wait_for_timeout(4000)

                for _ in range(12):
                    page.mouse.wheel(0, 3000)
                    page.wait_for_timeout(1500)

                selectors = [
                    'div[class*="detail_wbtext"]',
                    'div[class*="wbpro-text"]',
                    'div[class*="WB_text"]',
                    'div[dir="auto"]',
                ]
                hot_topics = []
                for selector in selectors:
                    elements = page.query_selector_all(selector)
                    valid_texts = [
                        el.inner_text().strip()
                        for el in elements
                        if len(el.inner_text().strip()) > 10
                    ]
                    if len(valid_texts) > 20:
                        hot_topics = valid_texts
                        break

                return "\n".join(hot_topics[:50])
            except Exception as exc:
                print(f"[weibo] scrape failed: {exc}")
                return ""
            finally:
                context.close()
                browser.close()

    def auto_checkin(self):
        print("[weibo] auto checkin")
        with sync_playwright() as p:
            browser = launch_chromium(p)
            context = browser.new_context()
            try:
                context.add_cookies(parse_cookie_string(self.cookie_str))
                page = context.new_page()
                page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)

                if page.get_by_text("已签到").count() > 0:
                    return True, "今天已经签到过了。"

                sign_btn = page.get_by_text("签到").first
                if sign_btn.count() > 0 and sign_btn.is_visible():
                    sign_btn.click()
                    page.wait_for_timeout(3000)
                    return True, "签到动作已触发。"
                return False, "未找到签到按钮。"
            except Exception as exc:
                return False, f"签到异常: {exc}"
            finally:
                context.close()
                browser.close()

    def publish_post(self, text_to_publish):
        print("[weibo] publish post")
        with sync_playwright() as p:
            browser = launch_chromium(p)
            context = browser.new_context()
            try:
                context.add_cookies(parse_cookie_string(self.cookie_str))
                page = context.new_page()
                page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

                join_btn = page.locator(
                    'a[action-type="follow"], a:has-text("加关注")'
                ).first
                if join_btn.count() > 0 and join_btn.is_visible():
                    join_btn.click()
                    page.wait_for_timeout(3000)
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(1000)

                input_box = page.locator(
                    "textarea[title='微博输入框'], textarea.W_input, textarea[placeholder*='有什么想和大家分享的']"
                ).first
                if input_box.count() > 0:
                    input_box.click()
                    input_box.fill(text_to_publish)
                    page.wait_for_timeout(3000)
                    send_btn = page.locator(
                        "a[title='发布'], a.W_btn_a, button:has-text('发布')"
                    ).first
                    if send_btn.count() > 0:
                        send_btn.click()
                        page.wait_for_timeout(3000)
            finally:
                context.close()
                browser.close()
