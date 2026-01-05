import sys
import json
from util.config import ClientConfig as Config

buffer_group = {}

"""
history_panel_situation_selector.py
主体 = Config.convert_to_traditional_chinese_main == "繁"
| 主体 | 真实情况 | 情况编号 |
|------|----------|----------|
| 简   | 简       | 1        |
|      | 反转     | 2        |
|      | 离线翻译 | 3        |
|      | 在线翻译 | 4        |
| 繁   | 繁       | 5        |
|      | 反转     | 6        |
|      | 离线翻译 | 7        |
|      | 在线翻译 | 8        |
"""


def situation_selector(opposite_state, offline_translate_needed, online_translate_needed):
    if Config.convert_to_traditional_chinese_main == "繁":
        if online_translate_needed:
            return 8
        elif offline_translate_needed:
            return 7
        elif opposite_state:
            return 6
        elif not opposite_state:
            return 5
    else:
        if online_translate_needed:
            return 4
        elif offline_translate_needed:
            return 3
        elif opposite_state:
            return 2
        elif not opposite_state:
            return 1


# 另一种写法（基数偏移法）, 理论上最轻量
'''
def situation_selector(opposite_state, online_translate_needed, offline_translate_needed):
    base = 5 if Config.convert_to_traditional_chinese_main == "繁" else 1
    if online_translate_needed:
        return base + 3
    elif offline_translate_needed:
        return base + 2
    elif opposite_state:
        return base + 1
    else:
        return base
'''


def update_buffer(key, value):
    global buffer_group
    buffer_group[key] = value.strip()


def flush_buffer():
    global buffer_group
    if buffer_group:
        sent_group = buffer_group.copy()
        # 核心：加标记 + 序列化 + 发送到stdout（管道）
        send_data = f"###LIST_A###{json.dumps(sent_group, ensure_ascii=False)}\n"
        # ensure_ascii=False：保留中文，避免序列化后中文变成\u编码
        # console.print(f"{send_data}")
        sys.stdout.write(send_data)
        buffer_group.clear()  # 清空暫存


# match 语句的用法：
def history_panel_output_selector(situation, text, traditional_text, offline_translated_text, online_translated_text):
    match situation:
        case 1:  # 简体
            update_buffer('simplified', text)
            if Config.output_traditional_when_simplified:
                update_buffer('traditional', traditional_text)

        case 6:  # 简体(反转)
            update_buffer('simplified', text)
            if Config.output_traditional_when_traditional_opposite_state:
                update_buffer('traditional', traditional_text)

        case 5:  # 繁体
            update_buffer('traditional', traditional_text)
            if Config.output_simplified_when_traditional:
                update_buffer('simplified', text)

        case 2:  # 繁体(反转)
            update_buffer('traditional', traditional_text)
            if Config.output_simplified_when_simplified_opposite_state:
                update_buffer('simplified', text)

        case 3:  # 离线翻译(简体)
            update_buffer('english', offline_translated_text)
            if Config.output_simplified_when_simplified_offline_translate:
                update_buffer('simplified', text)
            if Config.output_traditional_when_simplified_offline_translate:
                update_buffer('traditional', traditional_text)

        case 7:  # 离线翻译(繁体)
            update_buffer('english', offline_translated_text)
            if Config.output_simplified_when_traditional_offline_translate:
                update_buffer('simplified', text)
            if Config.output_traditional_when_traditional_offline_translate:
                update_buffer('traditional', traditional_text)

        case 4:  # 在线翻译(简体)
            update_buffer('english', online_translated_text)
            if Config.output_simplified_when_simplified_online_translate:
                update_buffer('simplified', text)
            if Config.output_traditional_when_simplified_online_translate:
                update_buffer('traditional', traditional_text)

        case 8:  # 在线翻译(繁体)
            update_buffer('english', online_translated_text)
            if Config.output_simplified_when_traditional_online_translate:
                update_buffer('simplified', text)
            if Config.output_traditional_when_traditional_online_translate:
                update_buffer('traditional', traditional_text)

    flush_buffer()


'''
# if-elif-else 语句的用法：
def history_panel_output_selector(situation,text,traditional_text, offline_translated_text, online_translated_text):
    if situation == 1:
    # 输出简体的时候
        update_buffer('simplified', text)

        if Config.output_traditional_when_simplified:
            update_buffer('traditional', traditional_text)

    elif situation == 6:
    # 输出简体(反转)的时候
        update_buffer('simplified', text)

        if Config.output_traditional_when_traditional_opposite_state:
            update_buffer('traditional', traditional_text)

    elif situation == 5:
    # 输出繁体的时候
        update_buffer('traditional', traditional_text)

        if Config.output_simplified_when_traditional:
            update_buffer('simplified', text)

    elif situation == 2:
    # 输出繁体(反转)的时候
        update_buffer('traditional', traditional_text)

        if Config.output_simplified_when_simplified_opposite_state:
            update_buffer('simplified', text)


    elif situation == 3:
    # 输出离线翻译(simplified)的时候
        update_buffer('english', offline_translated_text)

        if Config.output_simplified_when_simplified_offline_translate:
            update_buffer('simplified', text)
        if Config.output_traditional_when_simplified_offline_translate:
            update_buffer('traditional', traditional_text)

    elif situation == 7:
    # 输出离线翻译(traditional)的时候
        update_buffer('english', offline_translated_text)

        if Config.output_simplified_when_traditional_offline_translate:
            update_buffer('simplified', text)
        if Config.output_traditional_when_traditional_offline_translate:
            update_buffer('traditional', traditional_text)

    elif situation == 4:
    # 输出在线翻译(simplified)的时候
        update_buffer('english', online_translated_text)

        if Config.output_simplified_when_simplified_online_translate:
            update_buffer('simplified', text)
        if Config.output_traditional_when_simplified_online_translate:
            update_buffer('traditional', traditional_text)

    elif situation == 8:
    # 输出在线翻译(traditional)的时候
        update_buffer('english', online_translated_text)

        if Config.output_simplified_when_traditional_online_translate:
            update_buffer('simplified', text)
        if Config.output_traditional_when_traditional_online_translate:
            update_buffer('traditional', traditional_text)

    flush_buffer()
'''


'''
config.py
Config:
output_traditional_when_simplified
output_simplified_when_simplified_opposite_state
output_traditional_when_simplified_offline_translate
output_simplified_when_simplified_offline_translate
output_traditional_when_simplified_online_translate
output_simplified_when_simplified_online_translate

output_simplified_when_traditional
output_traditional_when_traditional_opposite_state
output_simplified_when_traditional_offline_translate
output_traditional_when_traditional_offline_translate
output_simplified_when_traditional_online_translate
output_traditional_when_traditional_online_translate
'''

