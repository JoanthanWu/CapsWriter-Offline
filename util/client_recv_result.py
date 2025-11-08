import json

import opencc
import websockets

from util.client_check_websocket import check_websocket
from util.client_cosmic import Cosmic, console
from util.client_hot_sub import hot_sub
from util.client_rename_audio import rename_audio
from util.client_strip_punc import strip_punc
from util.client_type_result import type_result
from util.client_write_md import write_md
from util.config import ClientConfig as Config

if not Cosmic.transcribe_subtitles:
    from util.client_translate_offline import translate_offline
    from util.client_translate_online import translate_online
import warnings

warnings.filterwarnings("ignore")


# ----------- smart_history_actions_panel -----------
# if Config.enabled_smart_history_actions_panel:
from util.smart_history_actions_panel import add_sentence_group

buffer_group = {}
def update_buffer(key, value):
    global buffer_group
    # 填入或更新元素
    buffer_group[key] = value.strip()


def flush_buffer():
    global buffer_group
    if buffer_group:
        sent_group = buffer_group.copy()   # 建立副本
        add_sentence_group(sent_group)     # 傳副本進去
        buffer_group = {}                  # 清空暫存
# ----------- smart_history_actions_panel -----------


async def recv_result():
    if not await check_websocket():
        return
    console.print("[green]连接成功\n")

    # --------------------------------------------------------测试数据
    update_buffer('simplified', "from-client_recv_result.py update_buffer 这是简体AAA")
    update_buffer('traditional', "from-client_recv_result.py update_buffer 繁體中文測試")
    update_buffer('english', "from-client_recv_result.py update_buffer This is EnglishAAA")
    flush_buffer()
    # 测试数据z
    test_groups = [
        {
            'traditional': "from-client_recv_result.py 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 ",
        },
        {
            'simplified': "from-client_recv_result.py 这是一个只有简体的例子CCC",
            'traditional': "",
            'english': ""
        },
        {
            'traditional': "from-client_recv_result.py 這是一個只有繁體的例子",
        },
        {
            'english': "from-client_recv_result.py This is an English only exampleA."
        }
    ]
    for group in test_groups:
        add_sentence_group(group)
    # 测试数据 ---------------------------------------------------

    try:
        while True:
            # 接收消息
            message = await Cosmic.websocket.recv()
            message = json.loads(message)
            text = message["text"]
            delay = message["time_complete"] - message["time_submit"]

            # 如果非最终结果，继续等待
            if not message["is_final"]:
                continue

            # 消除末尾标点
            text = strip_punc(text)

            # 热词替换
            text = hot_sub(text)
# ----------- smart_history_actions_panel -----------
            # if Config.enabled_smart_history_actions_panel:
            update_buffer('simplified', text)
# ----------- smart_history_actions_panel -----------

            # 简繁转换
            convert_to_traditional_chinese_done = False
            converter = opencc.OpenCC(Config.opencc_converter)
            traditional_text = converter.convert(text)
            convert_to_traditional_chinese_done = True

            # 离线翻译
            offline_translate_done = False
            if Cosmic.offline_translate_needed and not Cosmic.transcribe_subtitles:
                offline_translated_text = await translate_offline(text)
                offline_translate_done = True

# ----------- smart_history_actions_panel -----------
                # if Config.enabled_smart_history_actions_panel:
                update_buffer('english', offline_translated_text)
# ----------- smart_history_actions_panel -----------

                Cosmic.offline_translate_needed = False

            # 在线翻译
            online_translate_done = False
            if Cosmic.online_translate_needed and not Cosmic.transcribe_subtitles:
                online_translated_text = translate_online(text)
                online_translate_done = True

# ----------- smart_history_actions_panel -----------
                # if Config.enabled_smart_history_actions_panel:
                update_buffer('english', online_translated_text)
# ----------- smart_history_actions_panel -----------

                Cosmic.online_translate_needed = False

            if Config.save_audio:
                # 重命名录音文件
                file_audio = rename_audio(
                    message["task_id"], text, message["time_start"]
                )
            else:
                file_audio = None

            if Config.save_markdown:
                # 记录写入 md 文件
                match Config.convert_to_traditional_chinese_main:
                    case "繁":
                        write_md(traditional_text, message["time_start"], file_audio)
                    case _:
                        write_md(text, message["time_start"], file_audio)

            # 控制台输出
            console.print(f"    转录时延：{delay:.2f}s")
            console.print(f"    识别结果：[green]{text}")
            if offline_translate_done:
                console.print(f"    离线翻译结果：[green]{offline_translated_text}")
            if online_translate_done:
                console.print(f"    在线翻译结果：[green]{online_translated_text}")
            if convert_to_traditional_chinese_done and Cosmic.opposite_state:
                console.print(f"    简繁转换结果：[green]{traditional_text}")
            console.line()

            # 打字
            if offline_translate_done:
                await type_result(offline_translated_text)
                offline_translate_done = False
            elif online_translate_done:
                await type_result(online_translated_text)
                online_translate_done = False
            elif convert_to_traditional_chinese_done:
                # 根据'简/繁'转换设定,来选择输出内容的逻辑
                if Config.enable_double_click_opposite_state:
                    match Config.convert_to_traditional_chinese_main:
                        case "繁":
                            if Cosmic.opposite_state:
                                await type_result(text)
                            else:
                                await type_result(traditional_text)

# ----------- smart_history_actions_panel -----------
                                # if Config.enabled_smart_history_actions_panel:
                                update_buffer('traditional', traditional_text)
# ----------- smart_history_actions_panel -----------

                        case _:
                            if Cosmic.opposite_state:
                                await type_result(traditional_text)

# ----------- smart_history_actions_panel -----------
                                # if Config.enabled_smart_history_actions_panel:
                                update_buffer('traditional', traditional_text)
# ----------- smart_history_actions_panel -----------

                            else:
                                await type_result(text)
                else:
                    await type_result(text)
                convert_to_traditional_chinese_done = False


# ----------- smart_history_actions_panel -----------
                # if Config.enabled_smart_history_actions_panel:
                print(f"from-client_recv_result.py A: {buffer_group}")
                flush_buffer()
                print(f"from-client_recv_result.py B: {buffer_group}")
# ----------- smart_history_actions_panel -----------

            Cosmic.opposite_state = False
    except websockets.ConnectionClosedError:
        console.print("[red]连接断开\n")
    except websockets.ConnectionClosedOK:
        console.print("[red]连接断开\n")
    except Exception as e:
        print(e)
    finally:
        return


if __name__ == "__main__":
    None
