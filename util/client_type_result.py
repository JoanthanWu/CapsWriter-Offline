from config import ClientConfig as Config
import keyboard
import clipman
import platform
import asyncio


async def type_result(text):
    # 模拟粘贴
    if Config.paste:
        # 保存剪切板
        try:
            # 初始化剪贴板模块
            clipman.init()
            temp = clipman.get()
        except clipman.exceptions.ClipmanBaseException as e:
            temp = e
            print(e)

        # 复制结果
        clipman.set(text)

        # 粘贴结果
        if platform.system() == "Darwin":  # Mac
            keyboard.press(55)
            keyboard.press(9)
            keyboard.release(55)
            keyboard.release(9)
        else:
            if keyboard.is_pressed(Config.offline_translate_shortcut):
                keyboard.release(Config.offline_translate_shortcut)
            if keyboard.is_pressed(Config.online_translate_shortcut):
                keyboard.release(Config.online_translate_shortcut)
            keyboard.send("ctrl + v")

        # 还原剪贴板
        if Config.restore_clipboard_after_paste:
            await asyncio.sleep(0.1)
            clipman.set(temp)

    # 模拟打印
    else:
        keyboard.write(text)
