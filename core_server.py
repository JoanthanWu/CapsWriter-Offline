import os
import sys
import asyncio
from multiprocessing import Process, Manager
from platform import system

import websockets
from config import ServerConfig as Config
from util.server_cosmic import Cosmic, console
from util.server_check_model import check_model
from util.server_ws_recv import ws_recv
from util.server_ws_send import ws_send
from util.server_init_recognizer import init_recognizer
from util.empty_working_set import empty_current_working_set
from util.server_run_offline_translate_service import run_offline_translate_service
from util.server_run_online_translate_service import run_online_translate_service

# 确保 os.getcwd() 位置正确，用相对路径加载模型
BASE_DIR = os.getcwd()
os.chdir(BASE_DIR)
# BASE_DIR = os.path.dirname(__file__); os.chdir(BASE_DIR)


async def main():
    # 检查模型文件
    check_model()

    console.line(2)
    console.rule("[bold #d55252]CapsWriter Offline Server")
    console.line()
    console.print(
        f"项目地址：[cyan underline]https://github.com/HaujetZhao/CapsWriter-Offline",
        end="\n\n",
    )
    console.print(f"当前基文件夹：[cyan underline]{BASE_DIR}", end="\n\n")
    console.print(
        f"绑定的服务地址：[cyan underline]{Config.addr}:{Config.speech_recognition_port}",
        end="\n\n",
    )

    # 跨进程列表，用于保存 socket 的 id，用于让识别进程查看连接是否中断
    Cosmic.sockets_id = Manager().list()

    # 负责识别的子进程
    console.print("载入模块中，载入时长约 50 秒，请耐心等待...")
    recognize_process = Process(
        target=init_recognizer,
        args=(Cosmic.queue_in, Cosmic.queue_out, Cosmic.sockets_id),
        daemon=True,
    )
    recognize_process.start()
    Cosmic.queue_out.get()

    # 启动离线翻译 WebSocket服务器
    if Config.start_offline_translate_server:
        console.print("载入离线翻译模型中，载入时长约 20 秒，请耐心等待...")
        translate_offline_server_process = Process(target=run_offline_translate_service)
        translate_offline_server_process.start()

    # 启动在线翻译 DeepLX服务器
    if Config.start_online_translate_server:
        console.print("启动在线翻译 DeepLX 服务...")
        run_online_translate_service()

    console.rule("[green3]开始服务")
    console.line()

    # 清空物理内存工作集
    if system() == "Windows":
        empty_current_working_set()

    # 负责接收客户端数据的 coroutine
    recv = websockets.serve(
        ws_recv,
        Config.addr,
        Config.speech_recognition_port,
        subprotocols=["binary"],
        max_size=None,
    )

    # 负责发送结果的 coroutine
    send = ws_send()
    await asyncio.gather(recv, send)


def init():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # Ctrl-C 停止
        console.print("\n再见！")
    except OSError as e:  # 端口占用
        console.print(f"出错了：{e}", style="bright_red")
        console.input("...")
    except Exception as e:
        print(e)
    finally:
        Cosmic.queue_out.put(None)
        sys.exit(0)
        # os._exit(0)


if __name__ == "__main__":
    init()
