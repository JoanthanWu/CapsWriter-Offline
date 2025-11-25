@staticmethod
def check_libretranslate_service():
    """检查LibreTranslate服务是否可用"""
    import httpx

    from util.config import LibreTranslateConfig

    try:
        # 简单测试服务连通性
        response = httpx.get(LibreTranslateConfig.api, timeout=10)
        # print(f"服务状态码: {response.status_code}")
        # print(f"服务响应: {response.text[:200]}")
        return response.status_code == 200
    except Exception:
        # print(f"服务检查失败: {e}")
        return False


if __name__ == "__main__":
    print(check_libretranslate_service())
