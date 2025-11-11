import json

import httpx

from util.config import ClientConfig as Config
from util.config import DeepLXConfig as DeepLX


def translate_online(text):
    data = {
        "text": text,
        "source_lang": "auto",
        "target_lang": Config.online_translate_target_languages,
    }
    post_data = json.dumps(data)
    r = httpx.post(url=DeepLX.api, data=post_data, timeout=60).text
    # 将JSON字符串解析为Python字典
    data = json.loads(r)
    if data.get("code") != 200:
        return data.get(
            "message"
        )  # too many requests, your IP has been blocked by DeepL temporarily, please don't request it frequently in a short time
    # 获取alternatives数组中的第一个字符串
    first_alternative = data.get("alternatives", [])[0]
    # 输出第一个替代字符串
    return first_alternative


if __name__ == "__main__":
    print(f"{DeepLX.api}")
    text = "有朋自远方来，不亦乐乎"
    online_trans_text = translate_online(text)
    print(online_trans_text)
