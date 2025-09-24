import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import keyboard
from flask import sessions
from pycaw.pycaw import AudioUtilities

from util.client_cosmic import Cosmic
from util.client_pause_other_audio import audio_playering_app_name
from util.client_send_audio import send_audio
from util.client_send_signal_to_hint_while_recording import (
    send_signal_to_hint_while_recording,
)
from util.client_stream import stream_reopen
from util.config import ClientConfig as Config
from util.my_status import Status

task = asyncio.Future()
status = Status("开始录音", spinner="point")
pool = ThreadPoolExecutor()
pressed = False
released = True
event = Event()
restore_audio_playing_needed  = False
saved_result_for_restore_audio_playing_needed = False
double_clicked = False
is_short_duration = False
hold_mode_first_time_cancel_task = False
last_time_pressed = 0
last_time_released = 0
key_pressed = False
saved_result_for_offline_translate_needed = False
saved_result_for_online_translate_needed = False
sessions = []


def shortcut_correct(e: keyboard.KeyboardEvent):
    # 在我的 Windows 电脑上，left ctrl 和 right ctrl 的 keycode 都是一样的，
    # keyboard 库按 keycode 判断触发
    # 即便设置 right ctrl 触发，在按下 left ctrl 时也会触发
    # 不过，虽然两个按键的 keycode 一样，但事件 e.name 是不一样的
    # 在这里加一个判断，如果 e.name 不是我们期待的按键，就返回
    key_expect = keyboard.normalize_name(Config.speech_recognition_shortcut).replace(
        "left ", ""
    )
    key_actual = e.name.replace("left ", "")
    if key_expect != key_actual:
        return False
    return True


def mute_all_sessions():
    global sessions
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        process_name = session.Process and session.Process.name()
        # 排除 ffplay.exe
        if process_name != "ffplay.exe":
            volume = session.SimpleAudioVolume
            volume.SetMute(1, None)


def unmute_all_sessions():
    global sessions
    for session in sessions:
        process_name = session.Process and session.Process.name()
        # 排除 ffplay.exe
        if process_name != "ffplay.exe":
            volume = session.SimpleAudioVolume
            volume.SetMute(0, None)


def restore_audio_playing():
    # 恢復音频的播放
    global restore_audio_playing_needed, saved_result_for_restore_audio_playing_needed
    # 处理音频暂停相关逻辑
    restore_audio_playing_needed = saved_result_for_restore_audio_playing_needed

    if Config.pause_other_audio and restore_audio_playing_needed:
        keyboard.send("play/pause")
        restore_audio_playing_needed  = False


def translate_needed():
    # 确认是否需要翻译
    if (
        keyboard.is_pressed(Config.offline_translate_shortcut)
        and Config.use_offline_translate_function
    ):
        Cosmic.offline_translate_needed = True
    else:
        Cosmic.offline_translate_needed = False
    if (
        keyboard.is_pressed(Config.online_translate_shortcut)
        and Config.use_online_translate_function
    ):
        Cosmic.online_translate_needed = True
    else:
        Cosmic.online_translate_needed = False


def launch_task():
    # 开始任务时播放提示音
    import shutil

    if shutil.which("ffplay") and Config.play_start_music:
        from util.client_play_music import play_music

        play_music(Config.start_music_path, Config.start_music_volume)

    global hold_mode_first_time_cancel_task
    # 确认是否需要翻译
    # 改为独立调用
    # translate_needed()

    if (
        not double_clicked
        and Config.only_enable_microphones_when_pressed_record_shortcut
    ):
        # 重启音频流; 在双击情况下, 只在第一次的时候启动(单击模式)
        stream_reopen()
        Cosmic.stream.start()

    # 长按模式(hold_mode)双击功能 第二次重启不适用于上面的判断, 因此，需要下面来判断是否重启音频流
    # 长按模式(hold_mode)双击功能 確實需要第二次啓動音频流, 设计的时候就是如此, 因为会进行一次 start  cancel 的流程, 然后第二次啓動才是双击功能的录音
    elif (
        hold_mode_first_time_cancel_task
        and double_clicked
        and Config.only_enable_microphones_when_pressed_record_shortcut
    ):
        stream_reopen()
        Cosmic.stream.start()
        hold_mode_first_time_cancel_task = False
    # 记录开始时间
    t1 = time.time()

    # 将开始标志放入队列
    asyncio.run_coroutine_threadsafe(
        Cosmic.queue_in.put({"type": "begin", "time": t1, "data": None}), Cosmic.loop
    )

    # 录音时静音其他音频播放
    if Config.mute_other_audio:
        mute_all_sessions()

    # 录音时暂停其他音频播放 且 有音频正在播放
    global restore_audio_playing_needed, saved_result_for_restore_audio_playing_needed
    if Config.pause_other_audio and not restore_audio_playing_needed:
        # 针对双击导致停止和播放的指令过快的问题，增加了时间延迟
        if is_short_duration:
                # 试过的时间: 0.2✘; 0.3✘; 0.4✔; 0.5✔;1✔
                time.sleep(0.4)
                
        if process_name := audio_playering_app_name():
            if process_name != "ffplay.exe" :
                keyboard.send("play/pause")
                restore_audio_playing_needed  = True

            if not is_short_duration:
                saved_result_for_restore_audio_playing_needed = restore_audio_playing_needed

    # 恢復原狀：修復因 "saved_result_for_restore_audio_playing_needed" 變量導致播放器誤播的狀況(在已經本身停播的情況下)。
    if process_name is None and not Config.hold_mode:
        saved_result_for_restore_audio_playing_needed = False
        restore_audio_playing_needed = False

    # 通知录音线程可以向队列放数据了
    Cosmic.on = t1

    # 打印动画：正在录音
    status.start()

    # 启动识别任务
    global task
    task = asyncio.run_coroutine_threadsafe(
        send_audio(),
        Cosmic.loop,
    )


def cancel_task():
    # 通知停止录音，关掉滚动条
    Cosmic.on = False
    status.stop()

   # 取消音频静音
    if Config.mute_other_audio:
        unmute_all_sessions()

    # 发送取消任务的消息到队列
    asyncio.run_coroutine_threadsafe(
        Cosmic.queue_in.put({"type": "cancel", "time": time.time(), "data": None}),
        Cosmic.loop,
    )

    if Config.only_enable_microphones_when_pressed_record_shortcut:
        # 结束音频流
        Cosmic.stream.stop()
        Cosmic.stream.close()


def finish_task():
    global task

    # 通知停止录音，关掉滚动条
    Cosmic.on = False
    status.stop()

    # 通知结束任务
    asyncio.run_coroutine_threadsafe(
        Cosmic.queue_in.put(
            {"type": "finish", "time": time.time(), "data": None},
        ),
        Cosmic.loop,
    )

    # 取消音频静音
    if Config.mute_other_audio:
        unmute_all_sessions()

    # 结束任务时播放提示音
    import shutil

    if shutil.which("ffplay") and Config.play_stop_music:
        from util.client_play_music import play_music
        play_music(Config.stop_music_path, Config.stop_music_volume)

    if Config.only_enable_microphones_when_pressed_record_shortcut:
        # 结束音频流
        Cosmic.stream.stop()
        Cosmic.stream.close()


# =================单击模式======================


def click_mode(e: keyboard.KeyboardEvent):
    # 0. 原来的设计甚是巧妙巧妙, 但是我的功力有限，消化不良.
    # 1. 这里的设计思路是: 按下`录音键`只记录`按下时的时间标记`，然后根据`弹起来时的时间标记`和前面`按下时的时间标记`的 长短 进行判断应该进行哪一种行为.

    # 2. 这种方法可以处理以下的情况:
    # 2.1. 原来的设计: 使用`CapsLock`开启大小写的功能, 在单击模式下`未触发`录音模式之前,长按这个按键切换有机率失败，但是进行录音模式`之后`, 成功的几率极大.
    # 2.2. 这是因为: `def manage_task(e: Event): `它是按下按键就立刻开启任务，在开启任务之后才进行判断是否`长/短`按。这就是导致有几率失败的原因

    # 3. `長按` = 进行大小写切换的功能, 需要按键抬起后才能切换;
    # 3.1. 如果需要按下之后是根据按下(不需要抬起)的时间自动进行大小写切换的功能, 可以参考原来作者的代码`def count_down(e: Event):`

    # 4. 为了解决在 Windows 下按键会自动重复的问题 : key_pressed 变量用于追踪按键是否已经被按下并记录时间。当按键第一次被按下时，记录时间并将 key_pressed 设为 True，防止重复记录时间。当按键释放时，将 key_pressed 重新设为 False，允许下一次按键记录新的时间。
    
    # - [x] Bug6: 20250918: click_mode : "double_clicked" 改为常驻 → 导致 Config.enable_double_click_opposite_state 失效。
            # 解决方法: client_recv_result.py → 判断变量放到 async def recv_result() 后；client_shortcut_handler.py → 移除所有 Config.enable_double_click_opposite_state。

    # - [x] Bug4: 20250919: click_mode : "Shift + double_clicked / double_clicked" 可能导致恢复播放失败。
            # 解决方法-Bug4: 在 "elif (double_clicked and is_short_duration)" 中移除 restore_audio_playing()。

    # - [ ] 潜在改善点: 20250924: 假如有两个应用在运行, 其中第1个在播放，第2个在暂停, 那么我进行录音，第一个会被暂停，而第2个在录音期间依然会被播放(靜音)，不符合“暂停所有应用”的设想。
        # 思路: 
            # 1. 能否指定某应用暂停/播放？
            # 2. 如何判断应用是否在播放？需将 audio_playering_app_name() 的结果存入数组逐一判断。

    global \
        last_time_pressed, \
        last_time_released, \
        key_pressed, \
        double_clicked, \
        is_short_duration, \
        restore_audio_playing_needed 

    if e.event_type == keyboard.KEY_DOWN and not key_pressed:
        # 計算是否屬於短時間內雙击`錄音鍵`
        is_short_duration = (
            True if time.time() - last_time_released < Config.threshold else False
        )

        last_time_pressed = time.time()
        key_pressed = True

    elif e.event_type == keyboard.KEY_UP:
        last_time_released = time.time()

        # 记录是否有任务; 此处已改用变量:`double_clicked` 来判断任务是否进行中
        # on = Cosmic.on

        # 如果大于`Config.threshold`的值, 判定为`長按`, 就取消本栈启动的任务(`cancel_task()`)
        if last_time_released - last_time_pressed >= Config.threshold:
            # 函数`cancel_task()` : 他和我想象中的功能可能不一样
            # 我想象中的功能: `長按` = 进行大小写切换
            # 原来的功能: 可能是 中断并且不输出 已经录入的语音文字
            # 如果启动以下的函数`cancel_task()` : Bug 复现方法是 按一次`录音键`进入录音状态, 随后进行一次长按, 就会进入错乱状态.
            # 如果没有特殊的需求, 现在的状况可以满足 `長按` = 进行大小写切换 的功能
            # 否则需要进入函数`cancel_task()` 修改
            # cancel_task()

            # 判定为`長按`，发送原來的按键功能
            keyboard.send(Config.speech_recognition_shortcut)
            key_pressed = False
            return

        # 任务不在进行中, 且不判定为`短击`, 就开始任务, 同时标记 任务在进行中狀态
        elif not double_clicked and not is_short_duration:
            translate_needed()
            send_signal_to_hint_while_recording(
                True,
                is_short_duration,
                Cosmic.offline_translate_needed,
                Cosmic.online_translate_needed,
                Config.hold_mode,
            )
            launch_task()

            double_clicked = True
            key_pressed = False
            return

        # 任务在进行中, 且不判定为`短击`, 就结束和完成任务
        elif double_clicked and not is_short_duration:
            finish_task()
            send_signal_to_hint_while_recording(
                False,
                is_short_duration,
                Cosmic.offline_translate_needed,
                Cosmic.online_translate_needed,
                Config.hold_mode,
            )

            double_clicked = False
            key_pressed = False

            # 恢復音频的播放
            restore_audio_playing()
            return

        # 任务在进行中, 且为`短击`, 判定爲需要輸出 `簡/繁`, 并且结束函数
        elif (
            double_clicked and is_short_duration
        ):
            translate_needed()
            send_signal_to_hint_while_recording(
                True,
                is_short_duration,
                Cosmic.offline_translate_needed,
                Cosmic.online_translate_needed,
                Config.hold_mode,
            )

            Cosmic.opposite_state = not Cosmic.opposite_state
            key_pressed = False
            # return

        # print(f'世界的尽头!')


# ======================长按模式==================================


def hold_mode(e: keyboard.KeyboardEvent):
    """像对讲机一样，按下录音，松开停止"""
    # - [x] 改進: 20250918: 增加 key_pressed 变量避免函数重复触发。
    # - [x] 改進: 20250918: 去掉 Cosmic.on，改用 last_time_released & last_time_pressed 记录时间。

    # - [x] Bug1: 20250918: Hold Mode 下
    #       1. 单次按下/弹起录音键 < Config.threshold
    #       2. 双击录音键
    #     → 播放无法恢复。
        # - [x] 解決方法-Bug1 20250919: 双击 → 增加 saved_result_for_restore_audio_playing_needed 保存状态。
        # - [x] 解決方法-Bug1 20250919: < threshold → 恢复命令延后执行，独立成函数。

    # - [?] Bug2: 20250918: 改动后需观察是否仍有任务顺序错乱。

    # - [x] Bug3: 20250918: holdmode=true 时 shift+录音键(双击) 失效，输出简体中文；holdmode=false 正常。
        # 解決方法-Bug3: 20250919: 修改 Config.enable_double_click_opposite_state=false → 可英文输出。
        # 解決方法-Bug3: 20250919: 删除 hold_mode() 内的 enable_double_click_opposite_state → 变为中文输出，问题与该变量相关。
        # 解決方法-Bug3: 20250924: 引入 saved_result_for_offline_translate_needed 保存状态，避免 shift 被误判抬起。
        # - [?] 原因-Bug3: 可能与 shift/caps lock 状态牵连有关，需继续确认。

    # - [x] 更新 20250919: 更新 "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09"
        # 解決方法-更新: 20250924: 新模型无标点，需额外加载；最终的效果不如旧版，已还原。

    # - [x] Bug5: 20250919: hold_mode 下双击录音键可能不恢复播放。
        # 观察-Bug5: 调整 launch_task() 暂停逻辑后，仅出现过一次，需继续观察。
        # 观察-Bug5: 20250924: 快速三次操作导致第三次动作被吞，第二次抬起时错误暂停。
        # 解决方法-Bug5: 20250924: 在 launch_task() 中对快速第二次按下(is_short_duration)增加延迟，仅 hold_mode 应用。

        
    global \
        task, \
        key_pressed, \
        double_clicked, \
        last_time_pressed, \
        last_time_released, \
        hold_mode_first_time_cancel_task, \
        is_short_duration, \
        restore_audio_playing_needed, \
        saved_result_for_restore_audio_playing_needed, \
        saved_result_for_offline_translate_needed, \
        saved_result_for_online_translate_needed
    
    # 处理按键按下事件
    if e.event_type == "down":
        if not key_pressed:
            key_pressed = True  # 标记为已按下
            last_time_pressed = time.time()
            # 計算是否屬於短時間內按下`錄音鍵`
            is_short_duration = (last_time_pressed - last_time_released) < Config.threshold

            # 短時間內,按下第二次錄音鍵判定爲需要輸出 `簡/繁`
            if is_short_duration:
                double_clicked = True

            # 处理双击切换简/繁状态
            if double_clicked:
                Cosmic.opposite_state = not Cosmic.opposite_state

            translate_needed()
            send_signal_to_hint_while_recording(
                True,
                is_short_duration,
                Cosmic.offline_translate_needed,
                Cosmic.online_translate_needed,
                Config.hold_mode,
            )
            # 启动录音任务
            launch_task()
            saved_result_for_offline_translate_needed = Cosmic.offline_translate_needed
            saved_result_for_online_translate_needed = Cosmic.online_translate_needed

    elif e.event_type == "up":
        # 仅在已按下状态时处理松开事件
        if key_pressed:
            if is_short_duration:
                Cosmic.offline_translate_needed = saved_result_for_offline_translate_needed
                Cosmic.online_translate_needed = saved_result_for_online_translate_needed

            # 标记最后弹起的时间
            last_time_released = time.time()
            # 计算按键弹起来和按下的间隔
            duration = last_time_released - last_time_pressed
            # 取消或完成任务
            if duration < Config.threshold and not double_clicked:
                hold_mode_first_time_cancel_task = True
                cancel_task()

            else:
                finish_task()

                # 任务完成后, 还原释放案件的时间, 以免两个任务的时间间隔太短导致误判
                last_time_released = 0

                # 松开快捷键后，再按一次，恢复 CapsLock 或 Shift 等按键的状态
                if not double_clicked and Config.restore_key:
                    # time.sleep(0.01)
                    keyboard.send(Config.speech_recognition_shortcut)

                # 恢复輸出 `簡/繁` 原来的狀態， 恢复这个关于翻译的变量状态
                double_clicked = False
                saved_result_for_offline_translate_needed = False
                saved_result_for_online_translate_needed = False

            # 20250918: 增加了"key_pressed" 之后这里不应该向 AHK 发送 is_short_duration=True 的信号, 否则会导致"语音输入中"的提示不会进行取消 (跟AHK代码逻辑有关)， 最后，不影响AHK的提示。 
            send_signal_to_hint_while_recording(
                False,
                False,
                Cosmic.offline_translate_needed,
                Cosmic.online_translate_needed,
                Config.hold_mode,
            )

            # 恢復音频的播放
            restore_audio_playing()
            key_pressed = False  # 标记为未按下

# ==================== 绑定 handler ===============================


def hold_handler(e: keyboard.KeyboardEvent) -> None:
    # 验证按键名正确
    if not shortcut_correct(e):
        return

    # 长按模式
    hold_mode(e)


def click_handler(e: keyboard.KeyboardEvent) -> None:
    # 验证按键名正确
    if not shortcut_correct(e):
        return

    # 单击模式
    click_mode(e)


def bond_shortcut():
    if Config.hold_mode:
        keyboard.hook_key(
            Config.speech_recognition_shortcut, hold_handler, suppress=Config.suppress
        )
    else:
        # 单击模式，必须得阻塞快捷键
        # 收到长按时，再模拟发送按键
        keyboard.hook_key(
            Config.speech_recognition_shortcut, click_handler, suppress=True
        )
