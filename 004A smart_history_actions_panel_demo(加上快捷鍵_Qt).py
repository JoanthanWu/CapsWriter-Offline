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

        self.button = QPushButton("📋")
        self.button.setFixedSize(30, 30)
        self.button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: rgba(255,255,255,80);
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,150);
            }
        """)
        self.button.clicked.connect(self.copy_and_paste)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button, alignment=Qt.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self.adjustSize()

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
