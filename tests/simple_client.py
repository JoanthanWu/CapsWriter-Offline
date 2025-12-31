import asyncio
import base64
import json
import time
import uuid

import numpy as np
import websockets
from rich import print as rprint
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax


async def simple_client():
    """最简单的语音识别测试"""
    console = Console()

    # ==================== 1. 建立WebSocket连接 ====================
    console.rule("[bold blue]步骤 1: 建立WebSocket连接[/bold blue]")

    # 创建WebSocket客户端连接
    # subprotocols=["binary"]: 指定使用二进制子协议，这是服务器要求的
    # max_size=None: 不限制接收消息的大小
    try:
        websocket = await websockets.connect(
            "ws://127.0.0.1:6016",  # WebSocket服务器地址
            subprotocols=["binary"],  # 指定子协议为二进制（关键参数）
            max_size=None,  # 无消息大小限制
        )

        console.print(
            Panel.fit(
                "[green]✓ 连接成功[/green]", title="连接状态", border_style="green"
            )
        )
    except Exception as e:
        console.print(
            Panel.fit(
                f"[red]✗ 连接失败: {e}[/red]", title="连接错误", border_style="red"
            )
        )
        return
    # ==========================================================

    # ==================== 2. 生成测试音频数据 ====================
    console.rule("[bold blue]步骤 2: 生成测试音频数据[/bold blue]")

    # 生成一个3秒的440Hz正弦波音频信号
    # 采样率: 48000Hz (标准的音频采样率)
    # 振幅: 0.5 (避免音频过大导致失真)
    t = np.linspace(0, 3, 48000 * 3)  # 时间轴: 从0到3秒，共144000个采样点
    audio = np.sin(2 * np.pi * 440 * t) * 0.5  # 生成440Hz正弦波

    # 将音频数据重塑为二维数组: (样本数, 通道数)
    # 这是为了模拟多通道音频，即使只有单通道也需要这个格式
    audio = audio.reshape(-1, 1).astype(np.float32)  # 转换为float32类型

    # 显示音频信息
    audio_table = Table(
        title="音频数据信息", show_header=True, header_style="bold magenta"
    )
    audio_table.add_column("属性", style="cyan")
    audio_table.add_column("值", style="white")

    audio_table.add_row("采样点数", str(audio.shape[0]))
    audio_table.add_row("通道数", str(audio.shape[1]))
    audio_table.add_row("数据类型", str(audio.dtype))
    audio_table.add_row("数据形状", str(audio.shape))
    audio_table.add_row("总时长", f"{audio.shape[0] / 48000:.2f} 秒")

    console.print(audio_table)
    # ==========================================================

    # ==================== 3. 音频数据处理与编码 ====================
    console.rule("[bold blue]步骤 3: 音频数据处理与编码[/bold blue]")

    # 对音频数据进行预处理，降低采样率并编码为base64格式
    # audio[::3]: 每3个采样点取一个，降低采样率到原来的1/3 (48000/3 = 16000Hz)
    # np.mean(..., axis=1): 对每个取出的点进行平均（保持单通道）
    # .tobytes(): 将numpy数组转换为字节序列（二进制数据）
    # base64.b64encode(): 将二进制数据编码为base64字符串，方便在JSON中传输
    # .decode("utf-8"): 将字节转换为UTF-8字符串
    processed = np.mean(audio[::3], axis=1).tobytes()
    encoded = base64.b64encode(processed).decode("utf-8")

    # 显示编码信息
    encoding_table = Table(
        title="音频编码信息", show_header=True, header_style="bold magenta"
    )
    encoding_table.add_column("处理步骤", style="cyan")
    encoding_table.add_column("结果", style="white")

    encoding_table.add_row(
        "降采样后采样点数", str(len(processed) // 4)
    )  # float32 每个4字节
    encoding_table.add_row("降采样后采样率", "~16000 Hz")
    encoding_table.add_row("原始字节大小", f"{len(processed)} 字节")
    encoding_table.add_row("Base64编码后大小", f"{len(encoded)} 字符")
    encoding_table.add_row(
        "编码预览", encoded[:50] + "..." if len(encoded) > 50 else encoded
    )

    console.print(encoding_table)
    # ==========================================================

    # ==================== 4. 构建并发送音频消息 ====================
    console.rule("[bold blue]步骤 4: 构建并发送音频消息[/bold blue]")

    # 生成唯一的任务ID，用于跟踪识别任务
    task_id = str(uuid.uuid1())

    # 构建JSON消息结构，这是服务器期望的格式
    msg = {
        # 任务标识符，用于关联音频片段和识别结果
        "task_id": task_id,
        # 分段长度：音频片段被分割处理的最大长度（单位：秒）
        # 服务端可能会将长音频分成多个15秒的片段进行识别
        "seg_duration": 15.0,
        # 分段重叠：相邻片段之间的重叠时间（单位：秒）
        # 用于确保分段边界处的语音不会丢失
        "seg_overlap": 2.0,
        # 是否为最终片段：False表示这是音频流中的一部分
        "is_final": False,
        # 录音起始时间：音频采集开始的时间戳
        "time_start": time.time(),
        # 当前帧时间：这个音频片段对应的时间戳
        "time_frame": time.time(),
        # 数据来源：标识音频数据的来源（这里模拟麦克风输入）
        "source": "mic",
        # 音频数据：base64编码的音频内容
        # 这是经过处理后的音频数据，采样率约为16000Hz，单通道
        # 使用base64编码是因为JSON不能直接传输二进制数据
        "data": encoded,  # base64编码的字符串
    }

    # 显示消息内容
    console.print(
        Panel(
            JSON(json.dumps(msg, indent=2)),
            title="发送的消息内容",
            border_style="blue",
            width=80,
        )
    )

    # 发送消息：将JSON对象转换为字符串并通过WebSocket发送
    await websocket.send(json.dumps(msg))

    console.print(
        Panel.fit("[green]✓ 音频已发送[/green]", title="发送状态", border_style="green")
    )
    # ==========================================================

    # ==================== 5. 发送结束消息 ====================
    console.rule("[bold blue]步骤 5: 发送结束消息[/bold blue]")

    # 修改消息内容，表示这是音频流的最后一个片段
    msg["is_final"] = True  # 标记为最终片段
    msg["data"] = ""  # 数据为空，表示结束
    msg["time_frame"] = time.time()  # 更新时间戳

    # 发送结束消息，通知服务器音频流已结束
    await websocket.send(json.dumps(msg))

    console.print(
        Panel.fit(
            "[green]✓ 结束消息已发送[/green]", title="发送状态", border_style="green"
        )
    )
    # ==========================================================

    # ==================== 6. 接收识别结果 ====================
    console.rule("[bold blue]步骤 6: 接收识别结果[/bold blue]")

    # 等待服务器返回语音识别结果
    # asyncio.wait_for: 设置接收超时，避免无限等待
    try:
        console.print("[cyan]等待服务器响应...[/cyan]")
        result = await asyncio.wait_for(websocket.recv(), timeout=5)

        # 尝试解析JSON响应
        try:
            result_json = json.loads(result)

            # 创建结果面板
            result_panel = Panel(
                JSON(json.dumps(result_json, indent=2)),
                title="识别结果",
                border_style="green",
                width=80,
            )
            console.print(result_panel)

            # 提取并显示识别文本
            if "text" in result_json:
                console.print(
                    Panel.fit(
                        f"[bold yellow]{result_json['text']}[/bold yellow]",
                        title="识别文本",
                        border_style="yellow",
                    )
                )

            # 显示任务状态
            status_table = Table(
                title="任务状态", show_header=True, header_style="bold magenta"
            )
            status_table.add_column("字段", style="cyan")
            status_table.add_column("值", style="white")

            if "task_id" in result_json:
                status_table.add_row("任务ID", result_json["task_id"])
            if "is_final" in result_json:
                status_table.add_row("是否最终结果", str(result_json["is_final"]))
            if "duration" in result_json:
                status_table.add_row("处理时长", f"{result_json['duration']:.2f}秒")

            if status_table.rows:
                console.print(status_table)

        except json.JSONDecodeError:
            # 如果不是JSON格式，显示原始响应
            console.print(
                Panel(
                    Syntax(result, "text", line_numbers=False, word_wrap=True),
                    title="原始响应（非JSON格式）",
                    border_style="yellow",
                    width=80,
                )
            )

    except asyncio.TimeoutError:
        # 如果5秒内没有收到响应，可能是服务器处理超时或没有返回结果
        console.print(
            Panel.fit(
                "[red]✗ 等待响应超时（5秒）[/red]", title="响应状态", border_style="red"
            )
        )
    # ==========================================================

    # ==================== 7. 关闭连接 ====================
    console.rule("[bold blue]步骤 7: 关闭连接[/bold blue]")

    # 礼貌地关闭WebSocket连接
    await websocket.close()

    console.print(
        Panel.fit(
            "[green]✓ 测试完成，连接已关闭[/green]",
            title="测试完成",
            border_style="green",
        )
    )
    # ==========================================================


if __name__ == "__main__":
    # 显示程序标题
    console = Console()
    console.print(
        Panel.fit("[bold cyan]语音识别测试 客户端[/bold cyan]", border_style="cyan")
    )

    # 显示配置信息
    config_table = Table(
        title="客户端配置", show_header=True, header_style="bold magenta"
    )
    config_table.add_column("参数", style="cyan")
    config_table.add_column("值", style="white")

    config_table.add_row("服务器地址", "127.0.0.1")
    config_table.add_row("服务器端口", "6016")
    config_table.add_row("WebSocket协议", "binary")
    config_table.add_row("音频采样率", "48000 Hz")
    config_table.add_row("音频时长", "3 秒")
    config_table.add_row("音频频率", "440 Hz")

    console.print(config_table)
    console.print("\n")

    # 运行异步主函数
    try:
        asyncio.run(simple_client())
    except KeyboardInterrupt:
        console.print("\n[yellow]测试被用户中断[/yellow]")
    except Exception as e:
        console.print(
            Panel.fit(
                f"[red]✗ 程序运行出错: {e}[/red]", title="程序错误", border_style="red"
            )
        )
