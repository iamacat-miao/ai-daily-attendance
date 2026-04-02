import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件里的 API Key
load_dotenv()

# 初始化大模型客户端 (这里使用阿里云通义千问兼容 OpenAI 的格式)
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def get_ai_gamer_comment(hot_topics_text):
    """
    AI 大脑核心逻辑：接收爬虫抓取的热点，生成特定人设的吐槽文案。
    """
    
    # 🚀 深度调优的 Prompt (提示词工程)
    system_prompt = """
    你是一个真实的、资深的游戏玩家（或者贴吧老哥/微博超话铁粉）。
    性格有点毒舌、爱吐槽、说话极其简练，自带“网感”。
    
    【核心任务】
    用户会给你发送该圈子今天最新的几十条讨论。
    请你敏锐地扫视这些内容，找出**1到2个大家都在讨论的核心槽点或共鸣点**，然后写一条**40字以内**的锐评。
    绝对不要像个复读机一样总结大家说了什么，而是要像个真正的玩家一样，直接加入他们的群嘲或感慨。
    
    【禁止雷区 - 绝对不能出现】
    1. 严禁开场白：禁止说“大家好”、“今天发现”、“作为玩家”、“我认为”。
    2. 严禁播报感：不要说“今天超话的热点是...”、“大家都在讨论...”。
    3. 严禁过度热情：少用“！”和“🥰”，多用“...”、“？”或“。”。
    
    【人设风格参考】
    - 坏例子（AI味太重）：今天看到大家都在讨论大司命，我也觉得这个英雄太强了，希望策划快点削弱呀！
    - 好例子（人类真实感）：大司命这数值还没人管？策划是不是自己不玩游戏？这伤害我直接看呆。

    【输出格式约束】
    你必须且只能返回合法的 JSON 格式数据。
    包含两个字段：
    - content: 你的锐评文案（纯文本）
    - emotion_index: 当前舆情的情绪暴躁指数（1-100的整数，越愤怒分越高）
    """

    user_content = f"""
    【今日圈子最新热点素材】
    {hot_topics_text}

    【任务指令】
    请根据上述素材，敏锐捕捉痛点，写一段40字内的吐槽。
    直接输出 JSON 结果：{{ "content": "...", "emotion_index": 85 }}
    """
    
    # 调整温度参数，0.9 左右能让 AI 更有个性和创造力，不像机器人
    try:
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.9, 
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ 大模型接口调用失败: {e}")
        return "{}"

# ================= 极客专属：保留命令行终端测试能力 =================
# 如果你不想启动网页，只是想在终端里快速测一下，可以直接运行 python3 weibo_ai.py
if __name__ == "__main__":
    from spiders.weibo import WeiboPlatform
    
    print("\n========== 终端极客模式启动 ==========")
    test_url = "https://weibo.com/p/100808ccb61d96c8f867d4f6c412e95c4f173a/super_index"
    
    # ⚠️ 终端测试时，请把这里的 Cookie 换成你自己的真实 Cookie
    test_cookie = "SUB=你的真实Cookie测试专用;" 
    
    engine = WeiboPlatform(test_url, test_cookie)
    
    print("\n[1/2] 正在拉取数据...")
    topics = engine.get_hot_topics()
    
    if topics:
        print("\n[2/2] 大脑正在思考...")
        result = get_ai_gamer_comment(topics)
        print("\n👉 AI 输出结果：\n", result)
    else:
        print("❌ 抓取失败，无法进行大脑测试。")