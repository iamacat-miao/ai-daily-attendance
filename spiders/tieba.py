from playwright.sync_api import sync_playwright

from .base import BasePlatform
from .playwright_env import launch_chromium


def parse_tieba_cookie_string(cookie_str):
    cookies = []
    cookie_str = cookie_str.strip().strip('"').strip("'")
    for item in cookie_str.split(";"):
        if "=" in item:
            name, value = item.strip().split("=", 1)
            for domain in [".baidu.com", "tieba.baidu.com"]:
                cookies.append(
                    {"name": name, "value": value, "domain": domain, "path": "/"}
                )
    return cookies


class TiebaPlatform(BasePlatform):
    def get_hot_topics(self):
        print("[tieba] start scraping")
        with sync_playwright() as p:
            browser = launch_chromium(p)
            context = browser.new_context()
            try:
                context.add_cookies(parse_tieba_cookie_string(self.cookie_str))
                page = context.new_page()
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=45000)

                try:
                    page.wait_for_selector(".feed-list-container", timeout=10000)
                except Exception:
                    pass

                for _ in range(3):
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(1000)

                container = page.locator(".feed-list-container").first
                hot_topics = []
                items = container.locator(
                    ".thread-item, .thread-main, [class*='item--']"
                ).all()
                for item in items:
                    content_piece = item.locator(
                        ".title, .thread-content, [class*='content--'], [class*='title--']"
                    ).first
                    if content_piece.count() > 0:
                        text = content_piece.inner_text().strip()
                        if len(text) > 8:
                            hot_topics.append(text)

                if not hot_topics:
                    elements = container.locator("div, span").all()
                    hot_topics = [
                        el.inner_text().strip()
                        for el in elements
                        if 15 < len(el.inner_text().strip()) < 200
                    ]

                hot_topics = list(dict.fromkeys(hot_topics))
                return "\n".join(hot_topics[:50])
            except Exception as exc:
                print(f"[tieba] scrape failed: {exc}")
                return ""
            finally:
                context.close()
                browser.close()

    def auto_checkin(self):
        print("[tieba] auto checkin")
        with sync_playwright() as p:
            browser = launch_chromium(p)
            context = browser.new_context()
            try:
                context.add_cookies(parse_tieba_cookie_string(self.cookie_str))
                page = context.new_page()
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)

                signed_markers = ["已签到", "连签"]
                for marker in signed_markers:
                    locator = page.get_by_text(marker).first
                    if locator.count() > 0 and locator.is_visible():
                        return True, "今天已经签到过了。"

                sign_btn = page.locator("div.follow-sign").first
                if sign_btn.count() == 0:
                    sign_btn = page.get_by_text("签到", exact=True).first

                if sign_btn.count() > 0 and sign_btn.is_visible():
                    sign_btn.click()
                    page.wait_for_timeout(3000)
                    return True, "贴吧签到动作已触发。"
                return False, "未找到签到按钮。"
            except Exception as exc:
                return False, f"贴吧签到异常: {exc}"
            finally:
                context.close()
                browser.close()

    def publish_post(self, text_to_publish):
        print("[tieba] publish post")
        with sync_playwright() as p:
            browser = launch_chromium(p)
            context = browser.new_context()
            try:
                context.add_cookies(parse_tieba_cookie_string(self.cookie_str))
                page = context.new_page()
                page.goto(self.target_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

                trigger = page.locator(
                    ".button-wrapper--add-post, .add-btn, button:has-text('发帖'), i.icon-post"
                ).first
                if trigger.count() > 0:
                    trigger.click()
                    page.wait_for_timeout(2000)

                title_editor = page.locator("#tb-editor-title .ql-editor").first
                if title_editor.count() > 0:
                    title_text = text_to_publish[:25]
                    if len(title_text) < 5:
                        title_text = f"关于{title_text}的一点想法"
                    title_editor.click()
                    page.wait_for_timeout(500)
                    page.keyboard.type(title_text, delay=30)

                content_editor = page.locator("#tb-editor-content .ql-editor").first
                if content_editor.count() > 0:
                    content_editor.click()
                    page.wait_for_timeout(500)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.keyboard.type(text_to_publish, delay=10)
                    page.wait_for_timeout(2000)

                    submit_btn = page.locator(
                        ".issue-btn.button-wrapper--primary, button:has-text('发布')"
                    ).first
                    if submit_btn.count() > 0:
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(1000)
                        submit_btn.dispatch_event("click")
                        page.wait_for_timeout(5000)
            finally:
                context.close()
                browser.close()
