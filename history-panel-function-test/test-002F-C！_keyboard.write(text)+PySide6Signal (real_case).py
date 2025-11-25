import sys
import keyboard
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

class Config:
    hold_mode = True  # 可切换为 True 测试按住模式
    speech_recognition_shortcut = "u"  # 绑定的快捷键（单引号）
    suppress = True  # hold_mode 为 True 时的抑制配置

def input_chinese_text(e: keyboard.KeyboardEvent):
    """按下时触发的中文输入逻辑"""
    print(f"type0={e.event_type}")
    if e.event_type == 'down':
        # 按下时：触发输入逻辑（通过信号在主线程执行）
        print(f"type1={e.event_type}")
    elif e.event_type == 'up':
        print(f"type2={e.event_type}")


def hold_handler(event, signal):
    """按住模式处理器（按下和抬起均响应）"""
    signal.trigger_press.emit(event)


class KeyboardHandler(QObject):
    # 定义两个信号：分别处理按下和抬起事件
    trigger_press = Signal(keyboard.KeyboardEvent)  # 按下时触发

    def __init__(self):
        super().__init__()
        # 绑定信号与实际业务函数（确保主线程执行）
        self.trigger_press.connect(input_chinese_text)

        # 调用你的 bond_shortcut 逻辑（根据模式绑定处理器）
        self.bond_shortcut()

    def bond_shortcut(self):
        """融合你的源代碼：根据 hold_mode 绑定不同处理器"""
        if Config.hold_mode:
            # 按住模式：使用 hold_handler，suppress 由 Config 控制
            keyboard.hook_key(
                key=Config.speech_recognition_shortcut,
                # 回调函数需携带 signal 参数（当前 KeyboardHandler 实例）
                callback=lambda event: hold_handler(event, self),
                suppress=Config.suppress
            )
            print(f"已启用 [按住模式]，快捷键：{Config.speech_recognition_shortcut}（按下/抬起均响应）")


# ------------------------------
# 主窗口：显示模式信息
# ------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("融合 hold/click 模式的快捷键示例")
        self.layout = QVBoxLayout()
        mode_text = "按住模式（按下和抬起均有反应）" if Config.hold_mode else "单击模式（仅按下有反应）"
        self.label = QLabel(f"当前模式：{mode_text}\n"
                            f"快捷键：{Config.speech_recognition_shortcut}\n"
                            "操作：打开记事本并激活输入框，按快捷键测试")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.resize(400, 180)

        # 初始化键盘处理器（触发绑定逻辑）
        self.keyboard_handler = KeyboardHandler()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec())
    finally:
        keyboard.unhook_all()  # 退出时清理所有钩子
