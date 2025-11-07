# c_2.py :
from PySide6.QtCore import QThread, Signal
import keyboard

class KeyboardThread(QThread):
    trigger = Signal()

    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()

        keyboard.hook_key("/", handler, suppress=True)
        keyboard.wait()


if __name__ == "__main__":
    app, controller = b_2.run_app()

    # 觸發面板顯示
    controller.show_widgets_signal.emit()

    # 保持事件循環 → 視窗不會一閃而過
    app.exec()
