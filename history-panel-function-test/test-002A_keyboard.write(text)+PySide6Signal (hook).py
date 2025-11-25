import sys
import keyboard
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


# ------------------------------
# 普通函数：包含 keyboard.write(text)
# ------------------------------
def input_chinese_text():
    """普通函数：调用 keyboard.write 输入中文（示例文本）"""
    text = "我需要寫一段大串的中文文字,請問他可以做到嗎？"
    print(f"触发单引号键，即将输入：{text}")
    keyboard.write(text)  # 输入中文（需中文输入法激活）
    print("输入完成\n")


# ------------------------------
# 键盘事件处理器：用 hook_key 监听单引号键
# ------------------------------
class KeyboardHandler(QObject):
    # 信号：触发输入操作（确保主线程执行）
    trigger_input = Signal()

    def __init__(self):
        super().__init__()
        # 监听单引号键（'）的事件，回调函数接收 event 参数
        keyboard.hook_key(
            key="'",  # 单引号键的键名（直接用字符串表示）
            callback=self.on_quote_key_event  # 按键事件的回调
        )
        # 连接信号与普通函数（确保在主线程执行）
        self.trigger_input.connect(input_chinese_text)

    def on_quote_key_event(self, event):
        """
        hook_key 的回调函数（接收 event 参数）
        event 包含：event.event_type（'down' 或 'up'）、event.name（键名）等
        """
        # 只处理「按下」事件（避免释放时重复触发）
        if event.event_type == 'down':
            print(f"检测到单引号键按下（event: {event}）")
            # 发射信号，触发普通函数（在主线程执行）
            self.trigger_input.emit()


# ------------------------------
# 主窗口：提示操作步骤
# ------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("用 hook_key 监听单引号键")
        self.layout = QVBoxLayout()
        self.label = QLabel("操作步骤：\n"
                           "1. 打开记事本/文本编辑器并点击输入框（激活）\n"
                           "2. 确保输入法已切换到中文状态（如Ctrl+Shift）\n"
                           "3. 按下单引号键 ' → 触发中文输入")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.resize(400, 180)

        self.keyboard_handler = KeyboardHandler()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    #window.hide()
    try:
        sys.exit(app.exec())
    finally:
        keyboard.unhook_all()  # 退出时清理所有监听