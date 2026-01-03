# start.mp3 和 stop.mp3 播放没有声音时，用此脚本修复 ffplay.exe 音频播放

from pycaw.pycaw import AudioUtilities


def unmute_ffplay():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        process_name = session.Process and session.Process.name()
        print(process_name)
        if process_name == "ffplay.exe":
            volume = session.SimpleAudioVolume
            volume.SetMute(0, None)


if __name__ == "__main__":
    unmute_ffplay()
