import sys
import time
import pyautogui
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QTimer, QThread, Signal

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
        self.label.setStyleSheet("color: white; font-size: 20px;")

        # 三個小按鈕
        self.btn_copy = QPushButton("📑")      # Copy
        self.btn_paste = QPushButton("📋")     # Copy+Paste
        self.btn_type = QPushButton("✍️")      # 模擬打字

        for btn in (self.btn_copy, self.btn_paste, self.btn_type):
            btn.setFixedSize(18, 18)
            btn.setStyleSheet(self._button_style())

        self.btn_copy.clicked.connect(self.copy_only)
        self.btn_paste.clicked.connect(self.copy_and_paste)
        self.btn_type.clicked.connect(self.simulate_typing)

        # 右上角的水平工具列
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)  # 按鈕緊貼
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.btn_copy)
        button_layout.addWidget(self.btn_paste)
        button_layout.addWidget(self.btn_type)

        # 主佈局：左邊文字，右邊工具列
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.setLayout(main_layout)
        self.adjustSize()

    def _button_style(self):
        return """
            QPushButton {
                border: none;
                background-color: rgba(255,255,255,80);
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

    # 功能1：單純複製
    def copy_only(self):
        QApplication.clipboard().setText(self.label.text())
        print("已複製:", self.label.text())

    # 功能2：複製+貼上
    def copy_and_paste(self):
        QApplication.clipboard().setText(self.label.text())
        time.sleep(0.1)
        keyboard.send("ctrl + v")
        print("功能2：複製+貼上")
        self.close()

    # 功能3：模擬打字
    def simulate_typing(self):
        keyboard.write(self.label.text())
        print("功能3：模擬打字")
        self.close()

def show_widget():
    global current_widget
    if current_widget is None or not current_widget.isVisible():
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
        current_widget.set_text("更新後的文字")

    QTimer.singleShot(10000, current_widget.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widget)
    kb_thread.start()
    sys.exit(app.exec())
