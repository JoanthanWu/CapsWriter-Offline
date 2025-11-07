import sys
import time
import pyautogui
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QTimer

# 保存 widget 引用，避免被 GC
active_widgets = []

class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text

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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor(0, 0, 255, 128))  # 半透明藍色
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        super().paintEvent(event)

    def copy_and_paste(self):
        QApplication.clipboard().setText(self.text)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        self.close()

def show_widget(event):
    if event.event_type == "down":
        widget = RoundedWidget("這是一串浮動文字")
        widget.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        widget.setAttribute(Qt.WA_TranslucentBackground)
        widget.move(100, 100)
        widget.show()

        # 保存引用，避免被 GC
        active_widgets.append(widget)

        # 自動 3 秒後關閉
        QTimer.singleShot(3000, widget.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 註冊快捷鍵（非阻塞）
    keyboard.hook_key("z", show_widget, suppress=True)

    sys.exit(app.exec())
