import sys
import keyboard
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


# 配置类（模拟你的 Config）
class Config:
    hold_mode = True  # 切换模式：True=按住模式，False=单击模式
    speech_recognition_shortcut = "'"  # 绑定的快捷键（单引号）
    suppress = True  # hold_mode 时的抑制配置


# 键盘事件处理器（简化版）
class KeyboardHandler(QObject):
    # 仅保留一个信号：触发核心逻辑（按下/抬起的具体处理在其他函数中）
    trigger = Signal()

    def __init__(self):
        super().__init__()
        # 绑定信号到你的实际处理函数（假设已在其他地方定义）
        self.trigger.connect(self.your_actual_logic)  # 替换为你的实际处理函数
        self.bond_shortcut()  # 绑定快捷键

    def bond_shortcut(self):
        # 记录按键是否已按下（用于过滤长按重复事件）
        is_pressed = False  # 闭包变量，跟踪按键状态

        def callback(event):
            nonlocal is_pressed
            if event.event_type == 'down':
                if not is_pressed:  # 仅第一次按下时发射信号
                    self.trigger.emit()
                    is_pressed = True  # 标记为已按下
            else:  # 抬起时重置状态
                is_pressed = False

        if Config.hold_mode:
            keyboard.hook_key(
                key=Config.speech_recognition_shortcut,
                callback=callback,  # 使用带状态过滤的回调
                suppress=Config.suppress
            )
        else:
            # 单击模式同理，可复用上述 callback
            keyboard.hook_key(
                key=Config.speech_recognition_shortcut,
                callback=callback,
                suppress=True
            )

    def your_actual_logic(self):
        """你的实际处理函数（按下/抬起的逻辑在这里，已在其他地方实现）"""
        # 示例：这里可以调用你的核心逻辑（如输入中文、语音识别等）
        print("触发实际处理逻辑（按下/抬起的细节已在其他函数中实现）")
        """按下时触发的中文输入逻辑"""
        text = "我需要寫一段大串的中文文字,請問他可以做到嗎？"
        print(f"触发输入：{text}")
        keyboard.write(text)

# 主窗口（简化提示信息）
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简化版快捷键绑定")
        self.layout = QVBoxLayout()
        mode = "按住模式" if Config.hold_mode else "单击模式"
        self.label = QLabel(f"当前模式：{mode}\n快捷键：{Config.speech_recognition_shortcut}")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.resize(300, 120)

        self.keyboard_handler = KeyboardHandler()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec())
    finally:
        keyboard.unhook_all()