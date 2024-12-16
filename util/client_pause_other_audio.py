import time

import keyboard
from pycaw.pycaw import AudioUtilities


def audio_playering_app_name():
    # 不希望匹配的进程名称列表
    excluded_processes = [
        "123pan.exe",
        "msedge.exe",
    ]  # 123pan.exe 启动后始终在播放音频，不知道为什么。影响判断，把它排除掉
    # msedge.exe 暂停播放后,仍然告知系统在播放音乐,影响判断,把它排除掉

    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if (
            session.State == 1
            and session.Process is not None
            and session.Process.name() not in excluded_processes
        ):
            return session.Process.name()
    return None


def pause_other_audio():
    # 不希望匹配的进程名称列表
    excluded_processes = [
        "123pan.exe",
        "msedge.exe",
    ]  # 123pan.exe 启动后始终在播放音频，不知道为什么。影响判断，把它排除掉
    # msedge.exe 暂停播放后,仍然告知系统在播放音乐,影响判断,把它排除掉
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if (
            session.State == 1
            and session.Process is not None
            and session.Process.name() not in excluded_processes
        ):
            keyboard.send("play/pause")


if __name__ == "__main__":
    while True:
        if audio_playering_app_name() != None:
            print(f"Audio is currently playering by {audio_playering_app_name()} .")
            break
        else:
            print("No audio is playering.")
        time.sleep(1)
