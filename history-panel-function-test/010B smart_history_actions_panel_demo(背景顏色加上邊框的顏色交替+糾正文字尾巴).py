import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout
from PySide6.QtCore import Qt, QTimer, QThread, Signal

MAX_TOTAL = 12
pinned_sentences = []
unpinned_sentences = []
active_widgets = []
global_timer = None
PINNED_FILE = "pinned.json"

# 顏色組 A (Pinned)
PINNED_COLORS = [
    (QColor(255, 204, 102, 180), QColor(200, 100, 0)),   # A1: 背景橘 / 邊框深橘
    (QColor(255, 153, 153, 180), QColor(180, 50, 50)),   # A2: 背景粉紅 / 邊框紅
]

# 顏色組 B (Unpinned)
UNPINNED_COLORS = [
    (QColor(102, 178, 255, 180), QColor(0, 90, 180)),    # B1: 背景淺藍 / 邊框深藍
    (QColor(153, 255, 204, 180), QColor(0, 150, 100)),   # B2: 背景淺綠 / 邊框深綠
]

# -------------------
# 儲存 / 讀取 pinned
# -------------------
def save_pinned():
    with open(PINNED_FILE, "w", encoding="utf-8") as f:
        json.dump(pinned_sentences, f, ensure_ascii=False, indent=2)

def load_pinned():
    global pinned_sentences
    if os.path.exists(PINNED_FILE):
        with open(PINNED_FILE, "r", encoding="utf-8") as f:
            try:
                pinned_sentences = json.load(f)
            except Exception:
                pinned_sentences = []
    else:
        pinned_sentences = []


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

def reset_global_timer():
    """重置全局倒計時，時間到後關閉所有 widget"""
    global global_timer
    if global_timer is None:
        global_timer = QTimer()
        global_timer.setSingleShot(True)
        global_timer.timeout.connect(close_all_widgets)
    global_timer.start(5000)  # 5 秒

# -------------------
# 核心邏輯
# -------------------
def add_sentence(new_text):
    global unpinned_sentences
    if new_text in pinned_sentences:
        return
    unpinned_sentences.append(new_text)
    max_unpinned = MAX_TOTAL - len(pinned_sentences)
    while len(unpinned_sentences) > max_unpinned:
        removed = unpinned_sentences.pop(0)
        print("移除最舊未釘住:", removed)

def pin_sentence(text):
    global pinned_sentences, unpinned_sentences
    if text in pinned_sentences:
        pinned_sentences.remove(text)
        add_sentence(text)
        print("取消釘住:", text)
    else:
        pinned_sentences.append(text)
        if text in unpinned_sentences:
            unpinned_sentences.remove(text)
        max_unpinned = MAX_TOTAL - len(pinned_sentences)
        while len(unpinned_sentences) > max_unpinned:
            unpinned_sentences.pop(0)
        print("已釘住:", text)
    save_pinned()   # 每次更新都寫入檔案

def get_all_sentences():
    return pinned_sentences + unpinned_sentences

class MultiLineElidedLabel(QLabel):
    def __init__(self, text="", parent=None, max_lines=2, fixed_width=200, ellipsis="…"):
        super().__init__(text, parent)
        self.max_lines = max_lines
        self.fixed_width = fixed_width
        self.ellipsis = ellipsis
        self.setWordWrap(True)
        self.setFixedWidth(fixed_width)
        self.setText(text)

    def setText(self, text):
        fm = QFontMetrics(self.font())
        line_height = fm.lineSpacing()
        max_height = line_height * self.max_lines
        self.setFixedHeight(max_height)

        layout = QTextLayout(text, self.font())
        layout.beginLayout()
        lines = []
        more_lines_exist = False
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(self.fixed_width)
            start = line.textStart()
            length = line.textLength()
            lines.append(text[start:start + length])
            if len(lines) >= self.max_lines:
                # 還有更多行，但我們只取 max_lines
                if layout.createLine().isValid():
                    more_lines_exist = True
                break
        layout.endLayout()

        # 如果超過 max_lines，處理最後一行加 ellipsis
        if more_lines_exist:
            last_line = lines[-1]
            while last_line and fm.horizontalAdvance(last_line + self.ellipsis) > self.fixed_width:
                last_line = last_line[:-1]
            lines[-1] = last_line + self.ellipsis

        QLabel.setText(self, "\n".join(lines))


class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None, group="unpinned", index=0):
        super().__init__(parent)
        self.text = text
        self.group = group   # "pinned" 或 "unpinned"
        self.index = index   # 在該組內的順序

        # 使用自訂的 Label
        self.label = MultiLineElidedLabel(
            text,
            self,
            max_lines=2,
            fixed_width=200,
            ellipsis="[...]"
        )

        # 文字顏色以及大小
        self.label.setStyleSheet("color: white; font-size: 12px;")

        # 建立按鈕容器
        self.buttons_container = QWidget(self)
        btn_layout = QHBoxLayout(self.buttons_container)
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_pin = QPushButton("📌")
        self.btn_copy = QPushButton("📑")
        self.btn_paste = QPushButton("📋")
        self.btn_type = QPushButton("✍️")

        self.btn_pin.setObjectName("btn_pin")
        self.btn_copy.setObjectName("btn_copy")
        self.btn_paste.setObjectName("btn_paste")
        self.btn_type.setObjectName("btn_type")

        for btn in (self.btn_pin, self.btn_copy, self.btn_paste, self.btn_type):
            btn.setFixedSize(24, 20)
            btn_layout.addWidget(btn)

        # 綁定功能
        self.btn_pin.clicked.connect(self.pin_text)
        self.btn_copy.clicked.connect(self.copy_only)
        self.btn_paste.clicked.connect(self.copy_and_paste)
        self.btn_type.clicked.connect(self.simulate_typing)

        self.buttons_container.hide()

        # 主 layout
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(10, 10, 10, 10)

        # 套用樣式表
        self.setStyleSheet("""
            QPushButton {
                /* 普通按鈕的邊顏色以及背景顏色 */
                border: 1px solid rgba(246, 178, 107, 200);
                background-color: rgba(255, 204, 51, 200);
                padding: 0px;
                margin: 0px;
                /* 所有按鈕的大小 */
                font-size: 12px;
            }

            /* 釘住按鈕的基礎樣式 */
            QPushButton#btn_pin {
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                border-right: none;
            }
            QPushButton#btn_copy {
                border-radius: 0;
                border-right: none;
            }
            QPushButton#btn_paste {
                border-radius: 0;
                border-right: none;
            }
            QPushButton#btn_type {
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }

            /* 釘住狀態 */
            QPushButton#btn_pin[pinned="true"] {
                /* 已經釘住按鈕的背景顏色 */
                background-color: rgba(120, 63, 4, 250);
            }
            QPushButton#btn_pin[pinned="false"] {
                /* 未釘住按鈕的背景顏色 */
                background-color: rgba(255, 204, 51, 200);
            }

            /* hover 規則放在最後，確保其他按鈕也能生效 */
            QPushButton:hover {
                /* 鼠標在普通按鈕上面的轉換背景顏色 */
                background-color: rgba(255, 255, 153, 200);
            }
            QPushButton#btn_pin[pinned="true"]:hover {
                /* 鼠標在已經釘住按鈕上面的轉換背景顏色 */
                background-color: rgba(255, 255, 153, 200);
            }
            QPushButton#btn_pin[pinned="false"]:hover {
                /* 鼠標在未釘住按鈕上面的轉換背景顏色 */
                background-color: rgba(200,50,50,250);
            }
        """)

        # 初始化 pinned 屬性
        self.btn_pin.setProperty("pinned", "true" if self.text in pinned_sentences else "false")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)

    def resizeEvent(self, event):
        """讓按鈕容器固定在文字左上角"""
        super().resizeEvent(event)
        label_geo = self.label.geometry()
        self.buttons_container.move(label_geo.left(), label_geo.top())

    def enterEvent(self, event):
        """滑鼠進入文字 → 顯示按鈕"""
        self.buttons_container.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """滑鼠離開 → 隱藏按鈕"""
        self.buttons_container.hide()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        fm = self.label.fontMetrics()
        line_height = fm.lineSpacing()
        text = self.label.text()
        rect = fm.boundingRect(0, 0, self.label.width(), 9999, Qt.TextWordWrap, text)
        actual_lines = min(rect.height() // line_height, 2)

        padding_y = 10
        bg_height = actual_lines * line_height + padding_y * 2
        bg_width = self.label.width() + 20
        border_radius = 8

        # 選擇顏色組
        if self.group == "pinned":
            bg_color, border_color = PINNED_COLORS[self.index % 2]  # A1/A2 交替
        else:
            bg_color, border_color = UNPINNED_COLORS[self.index % 2]  # B1/B2 交替

        # 畫背景
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)

        # 畫邊框
        pen = QPen(border_color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)

        super().paintEvent(event)

    def copy_only(self):
        QApplication.clipboard().setText(self.text)
        print("已複製:", self.text)
        reset_global_timer()

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
        # 更新 pinned 屬性
        self.btn_pin.setProperty("pinned", "true" if self.text in pinned_sentences else "false")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)
        reset_global_timer()


def show_widgets():
    global active_widgets
    base_x, base_y = 100, 100
    y = base_y

    if active_widgets:
        close_all_widgets()
        return

    # pinned
    for i, text in enumerate(pinned_sentences):
        w = RoundedWidget(text, group="pinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, y)
        w.show()
        active_widgets.append(w)
        y += w.height()

    # unpinned
    for i, text in enumerate(unpinned_sentences):
        w = RoundedWidget(text, group="unpinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, y)
        w.show()
        active_widgets.append(w)
        y += w.height()


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
    # 啟動時讀取 pinned
    load_pinned()

    # 初始化一些句子
    for i in range(1, 13):
        add_sentence(f"第{i}句：這是測試文字 {chr(64+i)}")

    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widgets)
    kb_thread.start()

    # 模擬外部輸入
    # timer = QTimer()
    # timer.timeout.connect(simulate_new_sentence)
    # timer.start(5000)

    sys.exit(app.exec())

label = MultiLineElidedLabel(
    "這是一段非常非常非常非常非常非常非常非常長的文字，"
    "一定會超過兩行，最後一行應該會出現[...]",
    max_lines=2,
    fixed_width=200,
    ellipsis="[...]"
)
