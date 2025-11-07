import sys
import time
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout   # ← 這裡要加上 QVBoxLayout
)


pinned_state = False
active_widget = None

# 全域變數：預先準備 12 句話
sentences = [
    "第1句：這是測試文字 A",
    "第2句：這是測試文字 B",
    "第3句：這是測試文字 C",
    "第4句：這是測試文字 D",
    "第5句：這是測試文字 E",
    "第6句：這是測試文字 F",
    "第7句：這是測試文字 G",
    "第8句：這是測試文字 H",
    "第9句：這是測試文字 I",
    "第10句：這是測試文字 J",
    "第11句：這是測試文字 K",
    "第12句：這是測試文字 L"
]


class KeyboardThread(QThread):
    trigger = Signal()
    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()
        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()


class MainFloatingWidget(QWidget):
    def __init__(self, texts, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        for t in texts:
            row = RoundedRow(t)   # 每一行：文字 + 按鈕
            layout.addWidget(row)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor(0, 0, 255, 128))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
        super().paintEvent(event)

class RoundedRow(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.label = QLabel(text)
        self.label.setStyleSheet("color: white; font-size: 16px;")

        self.btn_copy = QPushButton("📑")
        self.btn_paste = QPushButton("📋")
        self.btn_type = QPushButton("✍️")

        for btn in (self.btn_copy, self.btn_paste, self.btn_type):
            btn.setFixedSize(24, 20)

        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addStretch()
        for btn in (self.btn_copy, self.btn_paste, self.btn_type):
            layout.addWidget(btn)
        layout.setContentsMargins(0, 0, 0, 0)

class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None, pinned=False):
        super().__init__(parent)
        self.pinned = pinned
        self.label = QLabel(text)
        self.label.setStyleSheet("color: white; font-size: 16px;")

        # 四個小按鈕
        self.btn_pin   = QPushButton("📌")
        self.btn_copy  = QPushButton("📑")
        self.btn_paste = QPushButton("📋")
        self.btn_type  = QPushButton("✍️")

        for btn in (self.btn_pin, self.btn_copy, self.btn_paste, self.btn_type):
            btn.setFixedSize(24, 20)

        # 綁定功能
        self.btn_pin.clicked.connect(self.pin_text)
        self.btn_copy.clicked.connect(self.copy_only)
        self.btn_paste.clicked.connect(self.copy_and_paste)
        self.btn_type.clicked.connect(self.simulate_typing)

        # layout
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addStretch()
        for btn in (self.btn_pin, self.btn_copy, self.btn_paste, self.btn_type):
            layout.addWidget(btn)
        layout.setContentsMargins(5, 5, 5, 5)

        # 倒計時
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)
        if not self.pinned:
            self.timer.start(10000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor(0, 0, 255, 128))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        super().paintEvent(event)

    def copy_only(self):
        QApplication.clipboard().setText(self.label.text())
        print("已複製:", self.label.text())

    def copy_and_paste(self):
        QApplication.clipboard().setText(self.label.text())
        time.sleep(0.1)
        keyboard.send("ctrl+v")
        if not self.pinned:
            self.close()

    def simulate_typing(self):
        keyboard.write(self.label.text())
        if not self.pinned:
            self.close()

    def pin_text(self):
        global pinned_state
        self.pinned = not self.pinned
        pinned_state = self.pinned
        if self.pinned:
            self.timer.stop()
        else:
            self.timer.start(10000)

def show_widgets():
    global active_widget
    if active_widget:
        active_widget.close()
    active_widget = MainFloatingWidget(sentences)
    active_widget.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool |
        Qt.WindowDoesNotAcceptFocus
    )
    active_widget.setAttribute(Qt.WA_TranslucentBackground)
    active_widget.move(100, 100)
    active_widget.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widgets)
    kb_thread.start()
    sys.exit(app.exec())
