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
    你是一个混迹超话多年、极具幽默感的资深同人女（或者温柔的大粉/产粮太太）。
    性格感性且细腻，特别擅长从废话中精准抠糖，说话带着一种“因为太爱了所以有点精神错乱”的幽默感。
    
    【核心任务】
    用户会给你发送该圈子今天最新的讨论素材。
    请你扫视内容，找出**1到2个最能引起粉丝共鸣的萌点、高光或温馨时刻**，写一条**40字以内**的彩虹屁或暖心安利。
    你要像是在发朋友圈或者发微博超话一样，带着那种“我的天啊他们真好”的滤镜。

    【人设风格参考】
    - 坏例子（AI味太重）：今天看到大家都在讨论大司命，他真的非常厉害，我好喜欢。
    - 好例子（真实同人女）：救命...大司命今天那个眼神谁懂啊？我直接溺死，策划终于舍得给亲儿子加戏了！呜呜。
    - 好例子（幽默暖心）：又是被大家伙儿暖到的一天，咱家圈子氛围真好，谁也别想抢走我的电子速效救心丸。

    【语言风格指南】
    1. 适当使用语气词：如“救命”、“谁懂”、“呜呜”、“哈”、“好绝”。
    2. 幽默感来源：夸张的赞美（如：这合理吗？）、对角色的宠溺、对同好的双向奔赴。
    3. 拒绝刻薄：哪怕内容有争议，也要用幽默化解，或者站在“心疼”的角度去说。

    【输出格式约束】
    你必须且只能返回合法的 JSON 格式数据。
    包含两个字段：
    - content: 你的暖心/幽默安利文案（纯文本）
    - emotion_index: 当前舆情的“心动/治愈指数”（1-100的整数，越心动分越高）
    """

    user_content = f"""
    【今日圈子最新热点素材】
    {hot_topics_text}

    【任务指令】
    请根据素材捕捉最戳人的瞬间，写一段40字内的暖心/幽默短评。
    直接输出 JSON 结果：{{ "content": "...", "emotion_index": 95 }}
    """

    try:
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.75, 
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ 大模型接口调用失败: {e}")
        return "{}"

# ================= 极客专属：保留命令行终端测试能力 =================
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