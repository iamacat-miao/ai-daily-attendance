import os


def configure_playwright_browser_path():
    """Use a project-local browser cache path that is writable on Streamlit Cloud."""
    browser_dir = os.path.join(os.getcwd(), ".playwright-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_dir
    os.makedirs(browser_dir, exist_ok=True)
    return browser_dir
