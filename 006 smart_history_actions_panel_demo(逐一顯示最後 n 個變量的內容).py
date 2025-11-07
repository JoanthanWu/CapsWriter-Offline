import sys
import time
import keyboard
from collections import deque
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QTimer, QThread, Signal

# 全域狀態
widgets = []                # 存放目前顯示中的 widget
recent_texts = deque(maxlen=5)  # 最後 n 個變量 (這裡 n=5，可自行調整)
pinned_state = False

class KeyboardThread(QThread):
    trigger = Signal()
    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()
        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()

class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None, pinned=False):
        super().__init__(parent)
        self.pinned = pinned
        self.label = QLabel(text)
        self.label.setStyleSheet("color: white; font-size: 20px;")

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
        layout.setContentsMargins(0, 0, 0, 0)

        # 設定 objectName
        self.btn_pin.setObjectName("btn_pin")
        self.btn_pin.setProperty("pinned", str(self.pinned).lower())

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
        self.btn_pin.setProperty("pinned", str(self.pinned).lower())
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)
        if self.pinned:
            self.timer.stop()
        else:
            self.timer.start(10000)

def show_widget():
    global widgets, recent_texts, pinned_state

    # 模擬一個會變化的變量
    new_text = f"變量值 {time.strftime('%H:%M:%S')}"
    recent_texts.append(new_text)

    # 建立新 widget
    w = RoundedWidget(new_text, pinned=pinned_state)
    w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
    w.setAttribute(Qt.WA_TranslucentBackground)

    # 排列位置：依照目前已有的 widget 數量往下疊
    base_x, base_y = 100, 100
    offset = 60
    w.move(base_x, base_y + offset * len(widgets))
    w.show()

    widgets.append(w)

    # 如果 deque 滿了，移除最舊的 widget
    if len(widgets) > recent_texts.maxlen:
        old = widgets.pop(0)
        old.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widget)
    kb_thread.start()
    sys.exit(app.exec())
