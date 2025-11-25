import sys
import keyboard
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from util.client_shortcut_handler import hold_mode, click_mode

# 配置类（模拟你的 Config）
class Config:
    hold_mode = True  # 切换模式：True=按住模式，False=单击模式
    speech_recognition_shortcut = "y"  # 绑定的快捷键（单引号）
    suppress = True  # hold_mode 时的抑制配置


# 键盘事件处理器（简化版）
class KeyboardHandler(QObject):
    # 仅保留一个信号：触发核心逻辑（按下/抬起的具体处理在其他函数中）
    trigger_hold_mode = Signal()
    trigger_click_mode = Signal()

    def __init__(self):
        super().__init__()
        # 绑定信号到你的实际处理函数（假设已在其他地方定义）
        self.trigger_hold_mode.connect(self.hold_mode)  # 替换为你的实际处理函数
        self.trigger_click_mode.connect(self.click_mode)  # 替换为你的实际处理函数
        self.bond_shortcut()  # 绑定快捷键

    def bond_shortcut(self):
        """根据模式绑定快捷键，简化回调逻辑"""
        if Config.hold_mode:
            # 按住模式：使用 Config 中的 suppress 配置，回调直接发射信号
            keyboard.hook_key(
                key=Config.speech_recognition_shortcut,
                callback=lambda event: self.trigger_hold_mode.emit(keyboard.KeyboardEvent),  # 直接发射信号
                suppress=Config.suppress
            )
            print(f"按住模式：快捷键 {Config.speech_recognition_shortcut} 已绑定")
        else:
            # 单击模式：强制 suppress=True，回调直接发射信号
            keyboard.hook_key(
                key=Config.speech_recognition_shortcut,
                callback=lambda event: self.trigger_click_mode.emit(keyboard.KeyboardEvent),  # 直接发射信号
                suppress=True
            )
            print(f"单击模式：快捷键 {Config.speech_recognition_shortcut} 已绑定")

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