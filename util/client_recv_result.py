import json
import warnings

import opencc
import websockets

from util.check_libretranslate_service import check_libretranslate_service
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

    if check_libretranslate_service():
        from util.client_translate_online_libretranslate import translate_online
    else:
        from util.client_translate_online import translate_online

warnings.filterwarnings("ignore")


# ----------- smart_history_actions_panel -----------
import sys
# if Config.enabled_smart_history_actions_panel:
# from . import smart_history_actions_panel
# add_sentence_group = smart_history_actions_panel.add_sentence_group
# from util.smart_history_actions_panel import smart_history_actions_panel
# add_sentence_group = smart_history_actions_panel.add_sentence_group

# import panelVal
# with open("history_r.log", "a", encoding="utf-8") as f:
    # f.write(f"in client_recv_result: id(panelVal.unpinned_groups) = {id(panelVal.unpinned_groups)})\n")

buffer_group = {}
def update_buffer(key, value):
    global buffer_group
    # 填入或更新元素
    buffer_group[key] = value.strip()


def flush_buffer():
    global buffer_group
    if buffer_group:
        sent_group = buffer_group.copy()   # 建立副本
        # add_sentence_group(sent_group)     # 傳副本進去
        # 核心：加标记 + 序列化 + 发送到stdout（管道）
        send_data = f"###LIST_A###{json.dumps(sent_group, ensure_ascii=False)}\n"
        # ensure_ascii=False：保留中文，避免序列化后中文变成\u编码
        #console.print(f"{send_data}")
        sys.stdout.write(send_data)
        buffer_group.clear()                  # 清空暫存
# ----------- smart_history_actions_panel -----------


async def recv_result():
    if not await check_websocket():
        return
    console.print("[green]连接成功\n")

    try:
        while True:
            # 接收消息
            message = await Cosmic.websocket.recv()
            message = json.loads(message)
            text = message["text"]
            delay = message["time_complete"] - message["time_submit"]

            # 如果非最终结果或文本为空，继续等待
            if not message["is_final"] or not text.strip():
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
                try:
                    file_audio = rename_audio(
                        message["task_id"], text, message["time_start"]
                    )
                except Exception:
                    file_audio = None
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
            flush_buffer()
# ----------- smart_history_actions_panel -----------

            Cosmic.opposite_state = False
    except websockets.ConnectionClosedError:
        console.print("[red]连接断开\n")
        from loguru import logger

        from util.safe_logger import init_logging

        init_logging()
        logger.error("连接断开，WebSocket连接关闭错误。")
    except websockets.ConnectionClosedOK:
        console.print("[red]连接断开\n")
        from loguru import logger

        from util.safe_logger import init_logging

        init_logging()
        logger.error("连接断开，WebSocket连接正常关闭。")
    except Exception as e:
        from loguru import logger

        from util.safe_logger import init_logging

        init_logging()
        logger.error(f"接收识别结果时出错: {e}")
    finally:
        return


if __name__ == "__main__":
    None
