import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QHBoxLayout, QVBoxLayout)
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout, QFont
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize

MAX_TOTAL = 12  # 最大显示组数
pinned_groups = []  # 存储钉住的组 {'simplified': '', 'traditional': '', 'english': ''}
unpinned_groups = []  # 存储未钉住的组
active_widgets = []
global_timer = None
PINNED_FILE = "pinned_groups.json"

# 颜色配置保持不变
PINNED_COLORS = [
    (QColor(155, 68, 0, 255), QColor(37, 73, 78)),   # #9B4400背景 / #25494E边框
    (QColor(179, 92, 68, 255), QColor(46, 107, 117)),   # #B35C44背景 / #2e6b75边框
]

UNPINNED_COLORS = [
    (QColor(44, 79, 84,255), QColor(137, 103, 71)),   # 高麗納戸色#2C4F54背景 / 896747边框
    (QColor(31, 49, 52,255), QColor(84, 67, 50)),   # 百入茶色#1F3134背景 / 544332边框
]

# -------------------儲存 / 讀取 pinned-------------------
def save_pinned():
    with open(PINNED_FILE, "w", encoding="utf-8") as f:
        json.dump(pinned_groups, f, ensure_ascii=False, indent=2)

def load_pinned():
    global pinned_groups
    if os.path.exists(PINNED_FILE):
        with open(PINNED_FILE, "r", encoding="utf-8") as f:
            try:
                pinned_groups = json.load(f)
            except Exception:
                pinned_groups = []
    else:
        pinned_groups = []

def close_all_widgets():
    global active_widgets
    for w in active_widgets[:]:
        w.close()
    active_widgets.clear()

def reset_global_timer():
    global global_timer
    if global_timer is None:
        global_timer = QTimer()
        global_timer.setSingleShot(True)
        global_timer.timeout.connect(close_all_widgets)
    global_timer.start(5000)  # 5 秒

# -------------------核心邏輯-------------------
def group_equal(group1, group2):
    if not isinstance(group1, dict) or not isinstance(group2, dict):
        return False
    keys = {'simplified', 'traditional', 'english'}
    for key in keys:
        val1 = group1.get(key, '').strip()
        val2 = group2.get(key, '').strip()
        if val1 != val2:
            return False
    return True

def add_sentence_group(new_group):
    global unpinned_groups
    for pg in pinned_groups:
        if group_equal(pg, new_group):
            return
    for ug in unpinned_groups:
        if group_equal(ug, new_group):
            return
    unpinned_groups.append(new_group)
    max_unpinned = MAX_TOTAL - len(pinned_groups)
    while len(unpinned_groups) > max_unpinned:
        removed = unpinned_groups.pop(0)
        print("移除最舊未釘住组")

def pin_sentence_group(group):
    global pinned_groups, unpinned_groups
    for i, pg in enumerate(pinned_groups):
        if group_equal(pg, group):
            pinned_groups.pop(i)
            add_sentence_group(group)
            print("取消釘住组")
            save_pinned()
            return
    pinned_groups.append(group)
    for i, ug in enumerate(unpinned_groups):
        if group_equal(ug, group):
            unpinned_groups.pop(i)
            break
    max_unpinned = MAX_TOTAL - len(pinned_groups)
    while len(unpinned_groups) > max_unpinned:
        unpinned_groups.pop(0)
    print("已釘住组")
    save_pinned()

def get_all_groups():
    return pinned_groups + unpinned_groups

class MultiLineElidedLabel(QLabel):
    def __init__(self, text="", parent=None, max_lines=2, fixed_width=200, ellipsis="…"):
        super().__init__(text, parent)
        self.max_lines = max_lines
        self.fixed_width = fixed_width
        self.ellipsis = ellipsis
        self.setWordWrap(True)
        self.setFixedWidth(fixed_width)

    def setText(self, text):
        fm = QFontMetrics(self.font())
        line_height = fm.lineSpacing()

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
                if layout.createLine().isValid():
                    more_lines_exist = True
                break
        layout.endLayout()

        if more_lines_exist and lines:
            last_line = lines[-1]
            while last_line and fm.horizontalAdvance(last_line + self.ellipsis) > self.fixed_width:
                last_line = last_line[:-1]
            lines[-1] = last_line + self.ellipsis

        actual_lines = len(lines)
        self.setFixedHeight(actual_lines * line_height)
        super().setText("\n".join(lines))


class RoundedWidget(QWidget):
    def __init__(self, sentence_group, parent=None, group="unpinned", index=0):
        super().__init__(parent)
        self.sentence_group = sentence_group  # 文字组
        self.group = group   # "pinned" 或 "unpinned"
        self.index = index   # 组内顺序

        # 【关键修复】先初始化钉住状态（移到创建文本行之前）
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)

        # 主文本布局（垂直排列各语言行）
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(6)  # 语言行之间的间距
        self.main_layout.setContentsMargins(10, 10, 10, 10)  # 整体内边距

        # 字体设置
        self.font = QFont()
        self.font.setPointSize(12)

        # 为每种文字创建"文本+按钮"行（只处理非空文本）
        self.create_text_line('simplified', '简体：')
        self.create_text_line('traditional', '繁体：')
        self.create_text_line('english', 'English：')

        # 初始化整体样式
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(246, 178, 107, 200);
                background-color: rgba(255, 204, 51, 200);
                padding: 0px;
                margin: 0px;
                font-size: 12px;
                width: 24px;
                height: 20px;
            }
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
            QPushButton#btn_pin[pinned="true"] {
                background-color: rgba(120, 63, 4, 250);
            }
            QPushButton#btn_pin[pinned="false"] {
                background-color: rgba(255, 204, 51, 200);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 153, 200);
            }
            QPushButton#btn_pin[pinned="true"]:hover {
                background-color: rgba(255, 255, 153, 200);
            }
            QPushButton#btn_pin[pinned="false"]:hover {
                background-color: rgba(200,50,50,250);
            }
        """)

        # 初始化钉住状态（组级别的钉住状态）
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)

        self.adjustSize()

    def create_text_line(self, key, title):
        """为指定语言创建一行：标题 + 文本 + 4个按钮"""
        text = self.sentence_group.get(key, '').strip()
        if not text:
            return  # 空文本不显示行

        # 行容器（水平布局）
        line_widget = QWidget()
        line_layout = QHBoxLayout(line_widget)
        line_layout.setSpacing(5)  # 行内元素间距
        line_layout.setContentsMargins(0, 0, 0, 0)

        # 1. 标题标签（如"简体："）
        title_label = QLabel(title)
        title_label.setFont(self.font)
        title_label.setStyleSheet("color: #ffffcc;")  # 浅色标题
        title_label.setFixedWidth(60)  # 固定标题宽度
        line_layout.addWidget(title_label)

        # 2. 文本内容标签
        content_label = MultiLineElidedLabel(
            text,
            max_lines=2,
            fixed_width=200,  # 文本宽度
            ellipsis="[...]"
        )
        content_label.setFont(self.font)
        content_label.setStyleSheet("color: white;")
        content_label.setText(text)
        line_layout.addWidget(content_label)

        # 3. 按钮组（4个按钮）
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # 创建4个按钮
        btn_pin = QPushButton("📌")
        btn_copy = QPushButton("📑")
        btn_paste = QPushButton("📋")
        btn_type = QPushButton("✍️")

        # 设置按钮ID和属性
        btn_pin.setObjectName("btn_pin")
        # 按钮的钉住状态与组级别一致
        btn_pin.setProperty("pinned", "true" if self.is_pinned else "false")
        btn_pin.style().unpolish(btn_pin)
        btn_pin.style().polish(btn_pin)

        # 绑定按钮功能（传递当前文本）
        btn_pin.clicked.connect(lambda: self.pin_group())  # 钉住是组级别操作
        btn_copy.clicked.connect(lambda: self.copy_only(text))
        btn_paste.clicked.connect(lambda: self.copy_and_paste(text))
        btn_type.clicked.connect(lambda: self.simulate_typing(text))

        # 添加按钮到布局
        for btn in [btn_pin, btn_copy, btn_paste, btn_type]:
            btn_layout.addWidget(btn)

        line_layout.addWidget(btn_container)

        # 将行添加到主布局
        self.main_layout.addWidget(line_widget)

    def _calc_background_size(self):
        """计算背景大小"""
        # 整体高度 = 内容高度 + 内边距
        content_height = self.main_layout.sizeHint().height()
        padding_y = 10  # 上下内边距总和
        bg_height = content_height + padding_y

        # 宽度固定（根据内容调整）
        bg_width = 420  # 增加宽度以容纳按钮
        return bg_width, bg_height

    def sizeHint(self):
        bg_width, bg_height = self._calc_background_size()
        return QSize(bg_width, bg_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_width, bg_height = self._calc_background_size()
        border_radius = 8

        # 调整widget大小
        if self.height() != bg_height:
            self.setFixedHeight(bg_height)
        if self.width() != bg_width:
            self.setFixedWidth(bg_width)

        # 选择颜色组
        if self.group == "pinned":
            bg_color, border_color = PINNED_COLORS[self.index % 2]
        else:
            bg_color, border_color = UNPINNED_COLORS[self.index % 2]

        # 画背景
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)

        # 画边框
        pen = QPen(border_color)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, bg_width - 2, bg_height - 2, border_radius, border_radius)

        super().paintEvent(event)

    # 以下为按钮功能实现（针对单种文字）
    def copy_only(self, text):
        QApplication.clipboard().setText(text)
        print(f"已複製: {text[:20]}...")
        reset_global_timer()

    def copy_and_paste(self, text):
        QApplication.clipboard().setText(text)
        time.sleep(0.1)
        keyboard.send("ctrl+v")
        close_all_widgets()

    def simulate_typing(self, text):
        keyboard.write(text)
        close_all_widgets()

    def pin_group(self):
        """组级别钉住操作（所有文字的钉住按钮同步状态）"""
        pin_sentence_group(self.sentence_group)
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)
        # 更新所有钉住按钮的状态
        for btn in self.findChildren(QPushButton, "btn_pin"):
            btn.setProperty("pinned", "true" if self.is_pinned else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        reset_global_timer()


def show_widgets():
    global active_widgets
    base_x, base_y = 100, 100
    current_y = base_y
    spacing = 15  # 组之间的间距

    if active_widgets:
        close_all_widgets()
        return

    # 显示钉住的组
    for i, group in enumerate(pinned_groups):
        w = RoundedWidget(group, group="pinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing

    # 显示未钉住的组
    for i, group in enumerate(unpinned_groups):
        w = RoundedWidget(group, group="unpinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing


# -------------------模擬外部數據-------------------
counter = 1
def simulate_new_group():
    global counter
    new_group = {
        'simplified': f"简体示例 {counter}：你们好吗？山上的小朋友",
        'traditional': f"繁體示例 {counter}：你們好嗎？山上的小朋友",
        'english': f"Example {counter}：How are you? The kids on the hill."
    }
    add_sentence_group(new_group)
    print(f"新增组 {counter}")
    counter += 1
    if active_widgets:
        close_all_widgets()
        show_widgets()

# -------------------按鍵監聽-------------------
class KeyboardThread(QThread):
    trigger = Signal()
    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()
        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()

if __name__ == "__main__":
    load_pinned()

    # 初始化测试数据
    test_groups = [
        {
            'simplified': "你们好吗？山上的小朋友",
            'traditional': "你們好嗎？山上的小朋友",
            'english': "How are you? The kids on the hill."
        },
        {
            'simplified': "这是一个只有简体的例子",
            'traditional': "",
            'english': ""
        },
        {
            'simplified': "",
            'traditional': "這是一個只有繁體的例子",
            'english': ""
        },
        {
            'simplified': "",
            'traditional': "",
            'english': "This is an English only example."
        }
    ]
    for group in test_groups:
        add_sentence_group(group)

    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widgets)
    kb_thread.start()

    # 模拟定时新增组（可选）
    # timer = QTimer()
    # timer.timeout.connect(simulate_new_group)
    # timer.start(8000)

    sys.exit(app.exec())