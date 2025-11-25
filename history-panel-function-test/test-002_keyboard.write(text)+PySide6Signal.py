import sys
import keyboard
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


class KeyboardHandler(QObject):
    # 信号：触发中文输入
    trigger_write_chinese = Signal(str)

    def __init__(self):
        super().__init__()
        # 注册快捷键：Ctrl+Alt+W → 触发中文输入
        keyboard.add_hotkey(
            hotkey='ctrl+alt+w',
            callback=self.on_trigger_write,
            args=("我需要寫一段大串的中文文字,請問他可以做到嗎？",)
        )


        # 连接信号到处理函数（确保在主线程调用，避免潜在冲突）
        self.trigger_write_chinese.connect(self.write_chinese_text)

    def on_trigger_write(self, text):
        """keyboard回调（后台线程），发射信号到主线程"""
        self.trigger_write_chinese.emit(text)

    def write_chinese_text(self, text):
        """在主线程执行keyboard.write（输入中文）"""
        # 提示：确保当前有可输入的窗口（如记事本、编辑器）处于激活状态
        print(f"即将输入中文：{text}")
        keyboard.write(text)  # 输入中文文本


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中文输入示例")
        self.layout = QVBoxLayout()
        self.label = QLabel("请先打开一个可输入的窗口（如记事本）\n"
                           "然后按下 Ctrl+Alt+W 触发中文输入\n"
                           "注意：需提前将输入法切换到中文状态！")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.resize(400, 150)

        self.keyboard_handler = KeyboardHandler()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec())
    finally:
        keyboard.unhook_all()  # 退出时清理快捷键