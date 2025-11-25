import sys
import keyboard
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


class Config:
    hold_mode = True
    speech_recognition_shortcut = "p"  # 快捷键：单引号
    suppress = True


class KeyboardHandler(QObject):
    trigger_press = Signal()
    trigger_release = Signal()

    def __init__(self):
        super().__init__()
        self.trigger_press.connect(self.on_press)
        self.trigger_release.connect(self.on_release)
        self.is_first_press = False  # 标记首次按下
        self.bond_shortcut()  # 初始挂钩

    def bond_shortcut(self):
        """挂钩快捷键"""
        keyboard.hook_key(
            key=Config.speech_recognition_shortcut,
            callback=lambda event: self.hold_handler(event),
            suppress=Config.suppress
        )

    def unbond_shortcut(self):
        """临时解除挂钩"""
        keyboard.unhook_key(Config.speech_recognition_shortcut)

    def hold_handler(self, event):
        if event.event_type == 'down' and not self.is_first_press:
            self.is_first_press = True
            self.trigger_press.emit()
        elif event.event_type == 'up' and self.is_first_press:
            self.is_first_press = False
            self.trigger_release.emit()

    def on_press(self):
        print("KEY_DOWN")
        # 关键：写入前解除挂钩，避免模拟事件被捕获
        self.unbond_shortcut()
        keyboard.write("KEY_DOWN")  # 此时模拟的按键不会触发钩子
        self.bond_shortcut()  # 写完后重新挂钩

    def on_release(self):
        print("KEY_UP")
        # 同理：写入前解除挂钩
        self.unbond_shortcut()
        keyboard.write("KEY_UP")
        self.bond_shortcut()  # 重新挂钩


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("解决 keyboard.write 循环触发问题")
        self.layout = QVBoxLayout()
        self.label = QLabel(f"快捷键：{Config.speech_recognition_shortcut}\n按住2秒后抬起，应输出一次KEY_DOWN和KEY_UP")
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
        keyboard.unhook_all()