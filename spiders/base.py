# spiders/base.py
class BasePlatform:
    def __init__(self, target_url, cookie_str):
        self.target_url = target_url
        self.cookie_str = cookie_str

    def get_hot_topics(self):
        """抓取热点（必须由子类实现）"""
        raise NotImplementedError("子类必须实现此方法")

    def publish_post(self, text_to_publish):
        """发布帖子（必须由子类实现）"""
        raise NotImplementedError("子类必须实现此方法")

    def auto_checkin(self):
        """自动签到（可选实现）"""
        return False, "该平台暂不支持自动签到"