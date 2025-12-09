# 启动在线翻译服务

# 测试
# .\runtime\python.exe .\util\client\translate_online.py


import subprocess

from util.config import DeepLXConfig as DeepLX


def run_online_translate_service():
    # 启动在线翻译服务端
    # 设置启动信息，用于隐藏窗口
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = subprocess.SW_HIDE
    deeplx_translate_server_proc = subprocess.Popen(
        [DeepLX.exe_path, "-port", DeepLX.online_translate_port],
        creationflags=subprocess.CREATE_NO_WINDOW,
        startupinfo=info,
    )  # https://github.com/OwO-Network/DeepLX/releases


if __name__ == "__main__":
    print(DeepLX.exe_path)
    run_online_translate_service()
