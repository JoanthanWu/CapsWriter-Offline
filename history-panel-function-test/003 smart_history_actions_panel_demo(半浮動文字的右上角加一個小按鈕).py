import sys
import time
import pyautogui
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt

class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text

        # 建立文字 Label
        self.label = QLabel(text)
        self.label.setStyleSheet("color: white; font-size: 24px;")

        # 建立按鈕 📋
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

        # 排版：文字 + 按鈕
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
        # 複製到剪貼簿
        QApplication.clipboard().setText(self.text)

        # 等待剪貼簿更新
        time.sleep(0.1)

        # 模擬 Ctrl+V
        pyautogui.hotkey("ctrl", "v")

        # 關閉視窗，釋放資源
        self.close()

def main():
    app = QApplication(sys.argv)

    widget = RoundedWidget("這是一串浮動文字")
    widget.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool |
        Qt.WindowDoesNotAcceptFocus   # 👈 不奪焦點
    )
    widget.setAttribute(Qt.WA_TranslucentBackground)

    widget.move(50, 50)
    widget.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
