import sys
import time
import pyautogui
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QTimer, QThread, Signal

# 全域唯一 widget
current_widget = None

class KeyboardThread(QThread):
    trigger = Signal()

    def run(self):
        def handler(e):
            if e.event_type == "down":  # 只在按下時觸發
                self.trigger.emit()

        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()


class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.label = QLabel(text)
        self.label.setStyleSheet("color: white; font-size: 24px;")

        # 按鈕1：複製+貼上
        self.button_paste = QPushButton("📋")
        self.button_paste.setFixedSize(20, 20)
        self.button_paste.setStyleSheet(self._button_style())
        self.button_paste.clicked.connect(self.copy_and_paste)

        # 按鈕2：單純複製
        self.button_copy = QPushButton("📑")
        self.button_copy.setFixedSize(20, 20)
        self.button_copy.setStyleSheet(self._button_style())
        self.button_copy.clicked.connect(self.copy_only)

        # 按鈕3：執行另一組代碼
        self.button_action = QPushButton("✍️")
        self.button_action.setFixedSize(20, 20)
        self.button_action.setStyleSheet(self._button_style())
        self.button_action.clicked.connect(self.run_other_code)

        # 佈局
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button_copy, alignment=Qt.AlignTop)
        layout.addWidget(self.button_paste, alignment=Qt.AlignTop)
        layout.addWidget(self.button_action, alignment=Qt.AlignTop)
        layout.setContentsMargins(10, 10, 0, 10)
        layout.setSpacing(0)

        self.setLayout(layout)

        self.adjustSize()

    def _button_style(self):
        return """
            QPushButton {
                border: none;
                background-color: rgba(255,255,255,80);
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,150);
            }
        """

    def set_text(self, text):
        self.label.setText(text)
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor(0, 0, 255, 128))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        super().paintEvent(event)

    # 功能1：複製+貼上
    def copy_and_paste(self):
        QApplication.clipboard().setText(self.label.text())
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        self.close()

    # 功能2：單純複製
    def copy_only(self):
        QApplication.clipboard().setText(self.label.text())
        print("已複製:", self.label.text())
        self.close()

    # 功能3：另一組代碼
    def run_other_code(self):
        print("⚡ 執行另一組代碼")
        keyboard.write("模擬手打文字")
        # 這裡放你要執行的邏輯
        # 例如：打開一個新視窗、呼叫 API、寫檔案...
        self.close()


    def set_text(self, text):
        """更新文字"""
        self.label.setText(text)
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor(0, 0, 255, 128))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        super().paintEvent(event)

    def copy_and_paste(self):
        QApplication.clipboard().setText(self.label.text())
        time.sleep(0.1)
        keyboard.send("ctrl + v")
        self.close()

def show_widget():
    global current_widget

    if current_widget is None or not current_widget.isVisible():
        # 第一次建立
        current_widget = RoundedWidget("這是一串浮動文字")
        current_widget.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        current_widget.setAttribute(Qt.WA_TranslucentBackground)
        current_widget.move(100, 100)
        current_widget.show()
    else:
        # 已存在 → 更新文字
        current_widget.set_text("更新後的文字")

    # 自動關閉
    QTimer.singleShot(3000, current_widget.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widget)
    kb_thread.start()
    sys.exit(app.exec())
