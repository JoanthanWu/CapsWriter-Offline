import time

from loguru import logger
from zai import ZhipuAiClient

from util.config import ClientConfig as Config
from util.safe_logger import init_logging


def ai_optimize_language_expression(text):
    start = time.time()
    if Config.zhipuai_api_key == "":
        print("智谱AI API密钥为空，请设置智谱AI API密钥，或者关闭AI优化语言表达功能。")
        return text, time.time() - start
    prompt: str = ""
    match Config.zhipuai_prompt_style:
        case "official":
            prompt = Config.zhipuai_prompt_official
        case "sweetheart":
            prompt = Config.zhipuai_prompt_sweetheart
        case "social":
            prompt = Config.zhipuai_prompt_social
        case "poetry":
            prompt = Config.zhipuai_prompt_poetry
        case "english":
            prompt = Config.zhipuai_prompt_english
        case _:
            print(
                f"不支持的 AI 提示风格：{Config.zhipuai_prompt_style}，请在 offical、sweetheart、social、poetry、english 中选择。"
            )
            return text, time.time() - start
    if prompt == "":
        print("AI 提示语不能为空，请检查配置文件。")
        print(f"当前提示风格：{Config.zhipuai_prompt_style}")
        return text, time.time() - start

    try:
        client = ZhipuAiClient(api_key=Config.zhipuai_api_key)
        response = client.chat.completions.create(
            model=Config.zhipuai_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
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
