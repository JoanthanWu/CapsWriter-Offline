from loguru import logger
from zai import ZhipuAiClient

from util.config import ClientConfig as Config
from util.safe_logger import init_logging
import time


def ai_optimize_language_expression(text):
    start = time.time()
    if Config.zhipuai_api_key == "":
        print("请设置智谱AI API密钥")
        return text, time.time() - start
    try:
        client = ZhipuAiClient(api_key=Config.zhipuai_api_key)
        response = client.chat.completions.create(
            model=Config.zhipuai_model,
            messages=[
                {
                    "role": "user",
                    "content": Config.zhipuai_prompt,
                },
                {
                    "role": "assistant",
                    "content": "当然，我将对语音转录生成的文本进行校对和润色，使其更加流畅、准确和易读。",
                },
                {"role": "user", "content": text},
            ],
            thinking={
                "type": "disabled",  # 不启用深度思考模式
            },
            stream=False,  # 不启用流式输出
            max_tokens=4096,  # 最大输出 tokens
            temperature=0.7,  # 控制输出的随机性
        )
        # 获取回复
        optimized_text = response.choices[0].message.content
        # 消除换行符
        optimized_text = optimized_text.replace("\n", "")
        return optimized_text, time.time() - start
    except Exception as e:
        print(f"AI优化语言表达时发生错误： {e}")
        init_logging()
        logger.error(f"AI优化语言表达时发生错误： {e}")
        return text, time.time() - start
