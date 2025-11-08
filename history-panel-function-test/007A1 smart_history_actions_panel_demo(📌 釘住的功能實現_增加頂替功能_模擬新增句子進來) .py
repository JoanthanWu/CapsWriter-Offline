import sys
import time
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QTimer, QThread, Signal

MAX_TOTAL = 12
pinned_sentences = []
unpinned_sentences = []
active_widgets = []

class KeyboardThread(QThread):
    trigger = Signal()
    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()
        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()

def close_all_widgets():
    global active_widgets
    for w in active_widgets[:]:
        w.close()
    active_widgets.clear()

def add_sentence(new_text):
    """新增句子，總數不超過 MAX_TOTAL"""
    global unpinned_sentences
    if new_text in pinned_sentences:
        return
    unpinned_sentences.append(new_text)
    max_unpinned = MAX_TOTAL - len(pinned_sentences)
    while len(unpinned_sentences) > max_unpinned:
        removed = unpinned_sentences.pop(0)
        print("移除最舊未釘住:", removed)

def pin_sentence(text):
    """切換釘住狀態"""
    global pinned_sentences, unpinned_sentences
    if text in pinned_sentences:
        # 取消釘住 → 放回 unpinned
        pinned_sentences.remove(text)
        add_sentence(text)
        print("取消釘住:", text)
    else:
        # 新增釘住
        pinned_sentences.append(text)
        if text in unpinned_sentences:
            unpinned_sentences.remove(text)
        # 調整 unpinned 上限
        max_unpinned = MAX_TOTAL - len(pinned_sentences)
        while len(unpinned_sentences) > max_unpinned:
            unpinned_sentences.pop(0)
        print("已釘住:", text)

def get_all_sentences():
    """回傳 pinned + unpinned，總數 <= MAX_TOTAL"""
    return pinned_sentences + unpinned_sentences

class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text
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
        QApplication.clipboard().setText(self.text)
        print("已複製:", self.text)
        close_all_widgets()

    def copy_and_paste(self):
        QApplication.clipboard().setText(self.text)
        time.sleep(0.1)
        keyboard.send("ctrl+v")
        close_all_widgets()

    def simulate_typing(self):
        keyboard.write(self.text)
        close_all_widgets()

    def pin_text(self):
        pin_sentence(self.text)
        if self.text in pinned_sentences:
            self.btn_pin.setStyleSheet("background-color: rgba(255,100,100,180);")
        else:
            self.btn_pin.setStyleSheet("")

def show_widgets():
    global active_widgets
    base_x, base_y = 100, 100
    offset = 60

    if active_widgets:
        close_all_widgets()
        return

    all_texts = get_all_sentences()
    for i, text in enumerate(all_texts):
        w = RoundedWidget(text)
        w.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.move(base_x, base_y + offset * i)
        w.show()
        active_widgets.append(w)

# -------------------
# 模擬外部句子逐漸進來
# -------------------
counter = 1
def simulate_new_sentence():
    global counter
    new_text = f"新句子 {counter}"
    add_sentence(new_text)
    print("新增:", new_text)
    counter += 1
    # 如果浮窗正在顯示 → 立即刷新
    if active_widgets:
        close_all_widgets()
        show_widgets()

if __name__ == "__main__":
    # 初始化一些句子
    for i in range(1, 13):
        add_sentence(f"第{i}句：這是測試文字 {chr(64+i)}")

    app = QApplication(sys.argv)

    # 啟動鍵盤監聽
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widgets)
    kb_thread.start()

    # 每 5 秒自動新增一個句子
    timer = QTimer()
    timer.timeout.connect(simulate_new_sentence)
    timer.start(5000)

    sys.exit(app.exec())
