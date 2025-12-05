# def audio_playering_app_name():
#     from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

#     sessions = AudioUtilities.GetAllSessions()
#     for session in sessions:
#         if session.Process:
#             process_name = session.Process.name()
#             meter = session._ctl.QueryInterface(IAudioMeterInformation)
#             peak_value = meter.GetPeakValue()
#             if peak_value > 0:  # 如果峰值电平大于 0，表示正在播放音频
#                 logger.info(f"Process Name: {process_name}, Peak Value: {peak_value}")
#                 return process_name
#     else:
#         return None


# def pause_other_audio():
#     import keyboard

#     keyboard.send("play/pause")


# if __name__ == "__main__":
#     import time

#     while True:
#         if process_name := audio_playering_app_name():
#             print(f"Audio is currently playering by {process_name} .")
#             pause_other_audio()
#         else:
#             print("No audio is playering.")
#         time.sleep(2)

import time
from typing import Dict, List

import keyboard
import win32api
import win32gui
import win32process
from loguru import logger
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

from util.safe_logger import init_logging


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
        "QQMusic.exe": {"hotkey": "ctrl+alt+f5", "name": "QQ音乐"},
        "CloudMusic.exe": {"hotkey": "ctrl+alt+f6", "name": "网易云音乐"},
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


def send_media_command_to_process(pid: int, command_name: str = "play_pause") -> int:
    """向后台窗口发送媒体控制命令，不改变焦点"""

    # 定义媒体控制命令
    APPCOMMAND_MEDIA_PLAY_PAUSE = 14
    APPCOMMAND_MEDIA_PLAY = 46
    APPCOMMAND_MEDIA_PAUSE = 47

    # 映射命令名称到对应的值
    command_map = {
        "play_pause": APPCOMMAND_MEDIA_PLAY_PAUSE,
        "play": APPCOMMAND_MEDIA_PLAY,
        "pause": APPCOMMAND_MEDIA_PAUSE,
    }

    if command_name not in command_map:
        raise ValueError(
            f"不支持的命令: {command_name}。支持的命令: {list(command_map.keys())}"
        )

    command_value = command_map[command_name]
    WM_APPCOMMAND = 0x0319

    target_hwnds = []  # 存储找到的所有窗口

    # 找到所有属于该进程的窗口
    def find_windows_callback(hwnd, param):
        try:
            window_pid = win32process.GetWindowThreadProcessId(hwnd)[1]
            if window_pid == pid and win32gui.IsWindowVisible(hwnd):
                # 获取窗口标题，确保不是空窗口
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 0:
                    # 检查窗口类名，排除工具栏等
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name not in [
                        "ToolbarWindow32",
                        "Shell_TrayWnd",
                        "Progman",
                    ]:
                        target_hwnds.append(hwnd)
        except Exception as e:
            print(f"处理窗口 {hwnd} 时出错: {e}")
            init_logging()

            logger.error(f"处理窗口 {hwnd} 时出错: {e}")
        return True  # 始终返回 True 以继续枚举

    win32gui.EnumWindows(find_windows_callback, None)

    success_count = 0

    for target_hwnd in target_hwnds:
        try:
            win32api.PostMessage(target_hwnd, WM_APPCOMMAND, 0, command_value * 0x10000)
            logger.info(f"已向窗口 {target_hwnd} 发送{command_name}命令")
            success_count += 1
        except Exception as e:
            print(f"向窗口 {target_hwnd} 发送{command_name}命令失败: {e}")
            init_logging()

            logger.error(f"向窗口 {target_hwnd} 发送{command_name}命令失败: {e}")

    return success_count


class AudioMonitor:
    """音频监控器，支持配置和管理多个程序"""

    def __init__(self, exclude_processes: List[str] = None):
        """
        初始化音频监控器

        Args:
            exclude_processes: 要排除的进程名列表（如 ["ffplay.exe"]）
        """
        self.ignored_pids = set()  # 被忽略的进程ID
        self.paused_history: list[int] = []
        self.exclude_processes = exclude_processes or []

        print(f"初始化完成，排除列表: {self.exclude_processes}")

    def get_audio_playing_apps(self, exclude_names: List[str] = None) -> Dict[int, str]:
        """获取所有正在播放音频的应用程序，可排除特定进程名"""
        if exclude_names is None:
            exclude_names = []

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

    def pause_audio_apps(self):
        """暂停音频程序"""
        playing_apps = self.get_audio_playing_apps(exclude_names=self.exclude_processes)
        if not playing_apps:
            logger.info("未检测到任何音频播放程序")
            return {}

        # 只保留一个 playing_apps 同样有Bug
        # keys = list(playing_apps.keys())
        # for key in keys[1:]:
        #     del playing_apps[key]

        results = {}
        for pid, process_name in playing_apps.items():
            success_count = send_media_command_to_process(pid, "pause")
            results[process_name] = (pid, success_count)

            if success_count > 0:
                # 记录暂停历史
                self.paused_history.append(pid)
                logger.info(
                    f"{process_name} (PID: {pid}): 已向 {success_count} 个窗口发送暂停指令"
                )
            else:
                logger.error(f"{process_name} (PID: {pid}): 未找到可发送按键的窗口")

        return results

    def restore_audio_apps(self):
        """恢复播放音频程序，可指定特定的PID或忽略某些PID"""

        for pid in self.paused_history:
            # 恢复播放
            send_media_command_to_process(pid, "play")
            logger.info(f"已恢复音频播放程序 (PID: {pid})")

        self.clear_history()

    def clear_history(self):
        """清空历史记录"""
        self.paused_history = []


if __name__ == "__main__":
    monitor = AudioMonitor(exclude_processes=["ffplay.exe"])
    while True:
        process = monitor.get_audio_playing_apps()
        print(f"正在播放音频的程序: {process}")
        time.sleep(2)
        monitor.pause_audio_apps()
        time.sleep(2)
        print(f"已暂停{monitor.paused_history}")
        time.sleep(2)
        monitor.restore_audio_apps()
        time.sleep(2)
        print(f"已恢复{monitor.paused_history}")
