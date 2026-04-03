import os


CHROMIUM_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-blink-features=AutomationControlled",
    "--disable-features=site-per-process",
]


def configure_playwright_browser_path():
    browser_dir = os.path.join(os.getcwd(), ".playwright-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_dir
    os.makedirs(browser_dir, exist_ok=True)
    return browser_dir


def launch_chromium(playwright):
    configure_playwright_browser_path()
    return playwright.chromium.launch(
        headless=True,
        chromium_sandbox=False,
        args=CHROMIUM_LAUNCH_ARGS,
    )
