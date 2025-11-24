import json

import httpx

from util.config import ClientConfig as Config
from util.config import DeepLXConfig as DeepLX


def check_deeplx_service():
    """检查DeepLX服务是否可用"""
    try:
        # 简单测试服务连通性
        response = httpx.get(DeepLX.api, timeout=10)
        print(f"服务状态码: {response.status_code}")
        print(f"服务响应: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"服务检查失败: {e}")
        return False


def translate_online(text):
    try:
        data = {
            "text": text,
            "source_lang": "auto",
            "target_lang": Config.online_translate_target_languages,
        }
        print(f"请求数据: {data}")
        print(f"API地址: {DeepLX.api}")

        post_data = json.dumps(data)

        # 添加headers和更详细的超时设置
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        response = httpx.post(
            url=DeepLX.api,
            data=post_data,
            headers=headers,
            timeout=30.0,  # 分别设置连接和读取超时
        )

        print(f"响应状态码: {response.status_code}")
        print(f"原始响应: {response.text}")

        # 尝试解析JSON
        data = json.loads(response.text)

        if data.get("code") == 200:
            alternatives = data.get("alternatives", [])
            if alternatives:
                return alternatives[0]
            else:
                return "翻译成功但没有返回替代文本"
        else:
            error_msg = data.get("message", "未知错误")
            return f"翻译错误: {error_msg}"

    except json.JSONDecodeError as e:
        return f"JSON解析错误: {e}，响应状态码: {response.status_code}。响应内容: {response.text[:100]}"
    except httpx.TimeoutException:
        return "请求超时，请检查网络连接"
    except httpx.ConnectError:
        return f"连接失败，无法访问 {DeepLX.api}"
    except Exception as e:
        return f"未知错误: {e}"


if __name__ == "__main__":
    print(f"DeepLX API: {DeepLX.api}")

    text = "有朋自远方来，不亦乐乎"
    online_trans_text = translate_online(text)
    print(f"翻译结果: {online_trans_text}")
