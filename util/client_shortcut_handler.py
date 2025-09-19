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
    print(f"restore_audio_playing  1. restore_audio_playing_needed:{restore_audio_playing_needed}")
    restore_audio_playing_needed = saved_result_for_restore_audio_playing_needed
    print(f"restore_audio_playing  2. restore_audio_playing_needed:{restore_audio_playing_needed}")
    if Config.pause_other_audio and restore_audio_playing_needed:
        keyboard.send("play/pause")
        print(f"restore_audio_playing  3. restore_audio_playing_needed:{restore_audio_playing_needed}")
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
    if Config.pause_other_audio and not restore_audio_playing_needed :
        if process_name := audio_playering_app_name():
            print(f"launch  1. Audio is currently playering by {process_name} .")
            print(f"launch  1. restore_audio_playing_needed:{restore_audio_playing_needed}")
            if process_name != "ffplay.exe" :
                keyboard.send("play/pause")
                # if process_name != None:
                restore_audio_playing_needed  = True
                print(f"launch  A. process_name: {process_name} .")
            # # 恢復原狀：修復因 "saved_result_for_restore_audio_playing_needed" 變量導致播放器誤播的狀況(在已經本身停播的情況下)。
            # if process_name is None:
            #     print(f"launch  B. process_name: {process_name} .")
            #     saved_result_for_restore_audio_playing_needed = False

            if not is_short_duration:
                saved_result_for_restore_audio_playing_needed = restore_audio_playing_needed
    print(f"launch  2. Audio is currently playering by {process_name} .")
    print(f"launch  2. restore_audio_playing_needed:{restore_audio_playing_needed}")

    # 恢復原狀：修復因 "saved_result_for_restore_audio_playing_needed" 變量導致播放器誤播的狀況(在已經本身停播的情況下)。
    if process_name is None:
        print(f"launch  B. process_name: {process_name} .")
        saved_result_for_restore_audio_playing_needed = False
        restore_audio_playing_needed = False
        print(f"launch  3. restore_audio_playing_needed:{restore_audio_playing_needed}")
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
    # # 恢復音频的播放
    # global restore_audio_playing_needed 
    # # 处理音频暂停相关逻辑
    # print(f"cancel  1. restore_audio_playing_needed:{restore_audio_playing_needed}")
    # restore_audio_playing_needed = saved_result_for_restore_audio_playing_needed
    # print(f"cancel  2. restore_audio_playing_needed:{restore_audio_playing_needed}")
    # if Config.pause_other_audio and restore_audio_playing_needed:
    #     keyboard.send("play/pause")
    #     restore_audio_playing_needed  = False



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

    # # 恢復音频的播放
    # global restore_audio_playing_needed 
    # # 处理音频暂停相关逻辑
    # restore_audio_playing_needed = saved_result_for_restore_audio_playing_needed
    # print(f"Finish.1 restore_audio_playing_needed:{restore_audio_playing_needed}")
    # if Config.pause_other_audio and restore_audio_playing_needed :
    #     keyboard.send("play/pause")
    #     restore_audio_playing_needed  = False
    # print(f"Finish.2 restore_audio_playing_needed:{restore_audio_playing_needed}")

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
    
    # 20250918: click_mode : "double_clicked" 变量 在此处函数中 改为常駐, 他会导致 Config.enable_double_click_opposite_state 这个配置项失效， 需要修正
    # Bug4: 20250919: click_mode : "Shift + double_clicked or double_clicked" 有機會導致恢復音頻播放失敗.. 原因不明，需要再跟进。 觀察: 先是停下播放之後，然後輸出文字後聽到一些聲音，但是很快就又停止了。 
    # 解决方法-Bug4: 函数: "elif (double_clicked and is_short_duration)" : 這裏的函數 "restore_audio_playing()" 不應該加進來，不需要。 
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
            print(f"A")
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
            # `double_clicked`变量 在此处函数中 改为常駐 因此不需要以下的config判断
            # if Config.enable_double_click_opposite_state:
            double_clicked = True
            key_pressed = False
            print(f"B")
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

            # if Config.enable_double_click_opposite_state:
            double_clicked = False
            key_pressed = False

            # 恢復音频的播放
            print(f"C1")
            restore_audio_playing()
            print(f"C2")
            return

        # 任务在进行中, 且为`短击`, 判定爲需要輸出 `簡/繁`, 并且结束函数
        elif (
            double_clicked and is_short_duration
            # and Config.enable_double_click_opposite_state
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

            # 恢復音频的播放
            print(f"D1")
            # 這裏的函數 "restore_audio_playing()" 不應該加進來，不需要。 
            # restore_audio_playing()
            print(f"D2")
            # return

        # print(f'世界的尽头!')


# ======================长按模式==================================

'''
def hold_mode(e: keyboard.KeyboardEvent):
    """像对讲机一样，按下录音，松开停止"""
    global \
        task, \
        double_clicked, \
        last_time_released, \
        hold_mode_first_time_cancel_task, \
        restore_audio_playing_needed 

    # 計算是否屬於短時間內按下`錄音鍵`
    is_short_duration = (
        True if time.time() - last_time_released < Config.threshold else False
    )

    # 短時間內,按下第二次錄音鍵判定爲需要輸出 `簡/繁`
    if is_short_duration and Config.enable_double_click_opposite_state:
        double_clicked = True
        if Config.pause_other_audio and not restore_audio_playing_needed :
            if process_name := audio_playering_app_name():
                if process_name != "ffplay.exe":
                    restore_audio_playing_needed  = True

    if e.event_type == "down" and not Cosmic.on:
        # 根據上一次是否短時間內(`is_short_duration`)按下錄音鍵,來判斷是否需要輸出 `簡/繁`
        if double_clicked and Config.enable_double_click_opposite_state:
            Cosmic.opposite_state = not Cosmic.opposite_state
        translate_needed()
        send_signal_to_hint_while_recording(
            True,
            is_short_duration,
            Cosmic.offline_translate_needed,
            Cosmic.online_translate_needed,
            Config.hold_mode,
        )
        # 记录开始时间
        launch_task()

    elif e.event_type == "up":
        # 标记最后弹起的时间
        last_time_released = time.time()
        # 记录持续时间，并标识录音线程停止向队列放数据
        duration = time.time() - Cosmic.on
        # 取消或停止任务
        if duration < Config.threshold and not double_clicked:
            hold_mode_first_time_cancel_task = True

            cancel_task()

        else:
            finish_task()
            # 松开快捷键后，再按一次，恢复 CapsLock 或 Shift 等按键的状态
            if not double_clicked and Config.restore_key:
                time.sleep(0.01)
                keyboard.send(Config.speech_recognition_shortcut)
            # 恢复輸出 `簡/繁` 原来的狀態
            if Config.enable_double_click_opposite_state:
                double_clicked = False

        send_signal_to_hint_while_recording(
            False,
            is_short_duration,
            Cosmic.offline_translate_needed,
            Cosmic.online_translate_needed,
            Config.hold_mode,
        )
'''
'''
def hold_mode(e: keyboard.KeyboardEvent):
    """像对讲机一样，按下录音，松开停止"""
    global task, double_clicked, last_time_released, key_pressed, last_time_pressed, is_short_duration
    global hold_mode_first_time_cancel_task, restore_audio_playing_needed 

    # 处理按键按下事件
    if e.event_type == keyboard.KEY_DOWN:
        # 仅在未按下状态时处理按下事件，防止重复触发
        if not key_pressed:
            key_pressed = True  # 标记为已按下
            last_time_pressed = time.time()  # 统一获取当前时间，避免多次调用
            # 计算是否属于短时间内按下录音键
            is_short_duration = (last_time_pressed - last_time_released) < Config.threshold

            # 处理双击逻辑
            if is_short_duration and Config.enable_double_click_opposite_state:
                double_clicked = True
                _handle_audio_pause()

            _handle_key_down(double_clicked, is_short_duration)
    
    # 处理按键松开事件（单独判断，不被key_pressed状态阻塞）
    elif e.event_type == keyboard.KEY_UP:
        # 仅在已按下状态时处理松开事件
        if key_pressed:
            last_time_released = time.time()  # 统一获取当前时间，避免多次调用
            # is_short_duration = (last_time_pressed - last_time_released) < Config.threshold
            _handle_key_up(last_time_pressed, is_short_duration)
            key_pressed = False  # 标记为未按下


def _handle_audio_pause():
    global restore_audio_playing_needed 
    """处理音频暂停相关逻辑"""
    if Config.pause_other_audio and not restore_audio_playing_needed :
        process_name = audio_playering_app_name()
        if process_name and process_name != "ffplay.exe":
            restore_audio_playing_needed  = True


def _handle_key_down(double_clicked, is_short_duration):
    """处理按键按下时的逻辑"""
    # 处理双击切换简/繁状态
    if double_clicked and Config.enable_double_click_opposite_state:
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


def _handle_key_up(last_time_pressed, is_short_duration):
    """处理按键松开时的逻辑"""
    global last_time_released, hold_mode_first_time_cancel_task, double_clicked
    
    # 更新最后松开时间
    # last_time_released = last_time_pressed
    # duration = last_time_released - last_time_pressed

    # 处理任务取消或完成
    if is_short_duration and not double_clicked:
        hold_mode_first_time_cancel_task = True
        cancel_task()
    else:
        finish_task()
        # 恢复按键状态
        if not double_clicked and Config.restore_key:
            time.sleep(0.01)
            keyboard.send(Config.speech_recognition_shortcut)
        # 重置双击状态
        if Config.enable_double_click_opposite_state:
            double_clicked = False

    # 发送录音结束信号
    send_signal_to_hint_while_recording(
        False,
        is_short_duration,
        Cosmic.offline_translate_needed,
        Cosmic.online_translate_needed,
        Config.hold_mode,
    )
'''

def hold_mode(e: keyboard.KeyboardEvent):
    """像对讲机一样，按下录音，松开停止"""
    # 改進: 20250918: 增加了 key_pressed 变量用于追踪按键是否已经被按下， 以免某些函数会被重复触发。
    # 改進: 20250918: 在此函数中, 取消了 Cosmic.on 的运用, 改为了 last_time_released & last_time_pressed 变量来进行时间的记录和计算.

    # Bug1: 20250918: 在Hold Mode下, 1. 如果按下和弹起`錄音鍵` 单次的時間小于< Config.threshold 以及 2.双击的功能, 会导致播放中的浏览器或者音乐播放器 *不会恢复播放* 的状态。
    #   解決方法-Bug1 20250919: 2.双击的功能: 不会回复播放的原因是因为第一次弹起來的時候, 恢復播放的时候会有一段空档期, 这段期间使用电平侦测-是否有应用在播放的方法就会失效。 解決方法是增加了 saved_result_for_restore_audio_playing_needed 变量来保存第一次的状态。 
    #   解決方法-Bug1 20250919: 1.小于< Config.threshold: 单次按下和弹起录音键 ， 就会快速的停止和恢复播放。但是这两个指令间隔的时间太短，导致恢复的命令被吞掉了，所以把恢复的命令放到最后，让他有更多的时间执行。 同时`def cancel_task()` 和 `def finish_task()` 里面的恢复播放命令被取消了，放到独立的函數里执行。 

    # Bug2: 20250918: 在上述的改动后 ，需要继续观察是否还会存在"任务顺序错乱"的情况。
    # Bug3: 20250918: holdmode = true: shift + 录音键(双击) 失效了, 变成了输出简体中文 。 holdmode = false: 正常。
    # 更新 20250919: 需要更新最新版本的 "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09"

    # Bug5: 20250919: hold_mode: 录音键(双击) 有機會導致不會恢復播放(原本已在播放)
    #    解決方法-Bug5: def launch_task(): "# 录音时暂停其他音频播放 且 有音频正在播放" 放回到中間之後, 只測試出一次沒有恢復播放的情況。 需要繼續觀察.. 
    global \
        task, \
        key_pressed, \
        double_clicked, \
        last_time_pressed, \
        last_time_released, \
        hold_mode_first_time_cancel_task, \
        is_short_duration, \
        restore_audio_playing_needed, \
        saved_result_for_restore_audio_playing_needed
    
    # 处理按键按下事件
    if e.event_type == "down":
        if not key_pressed:
            key_pressed = True  # 标记为已按下
            print(f"1. restore_audio_playing_needed:{restore_audio_playing_needed}")
            last_time_pressed = time.time()
            # 計算是否屬於短時間內按下`錄音鍵`
            is_short_duration = (last_time_pressed - last_time_released) < Config.threshold


            # 短時間內,按下第二次錄音鍵判定爲需要輸出 `簡/繁`
            if is_short_duration and Config.enable_double_click_opposite_state:
                double_clicked = True

            # 处理双击切换简/繁状态
            if double_clicked and Config.enable_double_click_opposite_state:
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

    elif e.event_type == "up":
        # 仅在已按下状态时处理松开事件
        if key_pressed:
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
                # 恢复輸出 `簡/繁` 原来的狀態
                if Config.enable_double_click_opposite_state:
                    double_clicked = False

            # 20250918: 这里不应该向 AHK 发送 is_short_duration=True 的信号, 否则会导致"语音输入中"的提示不会进行取消 (跟AHK代码逻辑有关)， 最后，不影响AHK的提示。 
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
            print(f"Last. restore_audio_playing_needed:{restore_audio_playing_needed}")

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
