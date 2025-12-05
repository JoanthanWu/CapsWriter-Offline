import time
from typing import Dict, List

import keyboard

# import win32api
# import win32gui
# import win32process
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

from util.config import ClientConfig as Config


def get_audio_playing_apps(exclude_names: List[str] = None) -> Dict[int, str]:
    """获取所有正在播放音频的应用程序，可排除特定进程名"""
    if exclude_names is None:
        exclude_names = ["ffplay.exe"]

    playing_apps = {}
    sessions = AudioUtilities.GetAllSessions()

    for session in sessions:
        if session.Process:
            process_name = session.Process.name()
            pid = session.Process.pid

            # 检查是否在排除列表中
            if process_name.lower() in [name.lower() for name in exclude_names]:
                continue

            try:
                meter = session._ctl.QueryInterface(IAudioMeterInformation)
                peak_value = meter.GetPeakValue()

                # 如果峰值电平大于 0，表示正在播放音频
                if peak_value > 0:
                    playing_apps[pid] = process_name
            except Exception:
                # 有些进程可能不支持获取峰值电平，跳过它们
                continue

    return playing_apps


def handle_special_media_apps(playing_apps):
    """
    处理特殊媒体应用的暂停逻辑，支持多个特殊应用同时播放

    Args:
        playing_apps: 正在播放的应用字典 {窗口标题: 进程名}

    Returns:
        tuple: (是否处理了特殊应用, 处理的特殊应用列表)
        处理的应用列表格式: [{"exe": "QQMusic.exe", "windows": ["窗口1", "窗口2"]}, ...]
    """
    special_apps_map = {
        "QQMusic.exe": {"hotkey": Config.QQMusic_global_pause_hotkey, "name": "QQ音乐"},
        "CloudMusic.exe": {
            "hotkey": Config.CloudMusic_global_pause_hotkey,
            "name": "网易云音乐",
        },
        "PotPlayerMini64.exe": {
            "hotkey": Config.PotPlayer_global_pause_hotkey,
            "name": "PotPlayer",
        },
    }

    # 按应用类型分组收集匹配的窗口
    matched_apps_by_type = {}
    for window_name, exe_name in list(playing_apps.items()):
        if exe_name in special_apps_map:
            if exe_name not in matched_apps_by_type:
                matched_apps_by_type[exe_name] = {
                    "config": special_apps_map[exe_name],
                    "windows": [],
                }
            matched_apps_by_type[exe_name]["windows"].append(window_name)

    # 如果没有匹配的特殊应用
    if not matched_apps_by_type:
        return False, []

    # 处理每种类型的应用并记录结果
    processed_apps = []

    for exe_name, app_info in matched_apps_by_type.items():
        # 发送快捷键暂停该类型应用
        if app_info["config"]["hotkey"] == "":
            print(
                f"未配置 {app_info['config']['name']} 的全局暂停快捷键，不暂停音频播放"
            )
        else:
            keyboard.send(app_info["config"]["hotkey"])
            # 记录处理的应用信息
            processed_apps.append(
                {
                    "exe": exe_name,
                    "name": app_info["config"]["name"],
                    "windows": app_info["windows"][:],  # 创建副本
                    "hotkey": app_info["config"]["hotkey"],
                }
            )
            # 从playing_apps中删除该类型的所有窗口
            for window_name in app_info["windows"]:
                if window_name in playing_apps:
                    playing_apps.pop(window_name)

    return True, processed_apps


if __name__ == "__main__":
    while True:
        playing_apps = get_audio_playing_apps()
        if len(playing_apps) > 0:
            print(f"{len(playing_apps)} 个程序正在播放音频: {playing_apps}")
        # 网易云音乐/QQ音乐 播放时 使用 播放器设置的 全局快捷键 暂停/恢复 播放
        has_processed, processed_apps = handle_special_media_apps(playing_apps)
        if has_processed:
            print(f"已处理 {len(processed_apps)} 个特殊应用: {processed_apps}")
        else:
            match len(playing_apps):
                case 0:
                    # print("没有正在播放音频的程序")
                    ...
                case 1:
                    print("✅")
                case _:
                    print(f"❗有 {len(playing_apps)} 个正在播放音频的程序")
        print()
        time.sleep(3)
