from libretranslatepy import LibreTranslateAPI

from util.config import ClientConfig as Config
from util.config import LibreTranslateConfig


def translate_online(text: str):
    try:
        lt = LibreTranslateAPI(LibreTranslateConfig.api)
        result = lt.translate(
            q=text, source="auto", target=Config.online_translate_target_languages
        )
        return result
    except Exception as e:
        return f"LibreTranslate 翻译失败: {e}"


if __name__ == "__main__":
    text = "有朋自远方来，不亦乐乎"
    online_trans_text = translate_online(text)
    print(f"翻译结果: {online_trans_text}")
