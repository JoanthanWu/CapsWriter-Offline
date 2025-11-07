import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QHBoxLayout, QVBoxLayout)
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout, QFont
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize

# -------------------新增：审查文件配置-------------------
REVIEW_FILE = "reviewed_lines.txt"  # 审查文件路径
reviewed_lines = set()  # 存储审查文件中的所有行（去重）


MAX_TOTAL = 12
pinned_groups = []
unpinned_groups = []
active_widgets = []
global_timer = None
PINNED_FILE = "pinned_groups.json"

# 跟踪鼠标在任意widget区域的数量
mouse_hover_count = 0


PINNED_COLORS = [
    (QColor(155, 68, 0, 255), QColor(37, 73, 78)),
    (QColor(179, 92, 68, 255), QColor(46, 107, 117)),
]

UNPINNED_COLORS = [
    (QColor(44, 79, 84,255), QColor(137, 103, 71)),
    (QColor(31, 49, 52,255), QColor(84, 67, 50)),
]

# -------------------新增：读取审查文件-------------------
def load_reviewed_lines():
    """读取审查文件内容到集合（去重，忽略空行）"""
    global reviewed_lines
    reviewed_lines = set()
    if not os.path.exists(REVIEW_FILE):
        # 若文件不存在，创建空文件
        with open(REVIEW_FILE, "w", encoding="utf-8") as f:
            pass
        return
    try:
        with open(REVIEW_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()  # 去除前后空格、换行符
                if line:  # 跳过空行
                    reviewed_lines.add(line)
        print(f"已加载审查文件，共 {len(reviewed_lines)} 条记录")
    except Exception as e:
        print(f"读取审查文件失败：{e}")


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


# -------------------核心邏輯：添加前先审查-------------------
def close_all_widgets():
    global active_widgets
    for w in active_widgets[:]:
        w.close()
    active_widgets.clear()

def reset_global_timer():
    global global_timer, mouse_hover_count
    if mouse_hover_count > 0:
        return
    if global_timer is None:
        global_timer = QTimer()
        global_timer.setSingleShot(True)
        global_timer.timeout.connect(close_all_widgets)
    if global_timer.isActive():
        global_timer.stop()
    global_timer.start(1000)


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

# -------------------修改：添加前检查审查文件-------------------
def add_sentence_group(new_group):
    """新增组前先检查是否存在于审查文件，若存在则不添加"""
    global unpinned_groups

    # 1. 检查新组的所有文字是否在审查列表中
    for key in ['simplified', 'traditional', 'english']:
        text = new_group.get(key, '').strip()
        if text and text in reviewed_lines:  # 非空且存在于审查文件
            print(f"审查拦截：'{text}' 已在审查列表中，不添加")
            return  # 直接返回，不添加该组

    # 2. 原有逻辑：检查是否已存在于pinned或unpinned
    for pg in pinned_groups:
        if group_equal(pg, new_group):
            return
    for ug in unpinned_groups:
        if group_equal(ug, new_group):
            return

    # 3. 通过审查，添加到未钉住组
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


class TextLineWidget(QWidget):
    def __init__(self, text, title, is_pinned, parent=None):
        super().__init__(parent)
        self.text = text
        self.parent_widget = parent
        self.is_pinned = is_pinned

        self.line_layout = QHBoxLayout(self)
        self.line_layout.setSpacing(5)
        self.line_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("SimHei", 12))
        self.title_label.setStyleSheet("color: #ffffcc;")
        #self.title_label.setFixedWidth(30)
        self.line_layout.addWidget(self.title_label)

        self.content_label = MultiLineElidedLabel(
            text,
            max_lines=2,
            fixed_width=200,
            ellipsis="[...]"
        )
        self.content_label.setFont(QFont("SimHei", 12))
        self.content_label.setStyleSheet("color: white;")
        self.content_label.setText(text)
        self.line_layout.addWidget(self.content_label)

        self.buttons_container = QWidget(self)
        self.buttons_container.setStyleSheet("")
        self.buttons_container.hide()

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

        self.btn_pin.setProperty("pinned", "true" if self.is_pinned else "false")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)

        self.btn_pin.clicked.connect(self.pin_group)
        self.btn_copy.clicked.connect(self.copy_only)
        self.btn_paste.clicked.connect(self.copy_and_paste)
        self.btn_type.clicked.connect(self.simulate_typing)

        for btn in [self.btn_pin, self.btn_copy, self.btn_paste, self.btn_type]:
            btn.setFixedSize(24, 20)
            btn_layout.addWidget(btn)

        self.buttons_container.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        label_pos = self.content_label.pos()
        self.buttons_container.move(label_pos.x(), label_pos.y())
        self.buttons_container.setFixedSize(self.buttons_container.sizeHint())

    def enterEvent(self, event):
        self.buttons_container.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.buttons_container.hide()
        super().leaveEvent(event)

    def copy_only(self):
        QApplication.clipboard().setText(self.text)
        print(f"已複製: {self.text[:20]}...")
        reset_global_timer()

    def copy_and_paste(self):
        QApplication.clipboard().setText(self.text)
        time.sleep(0.1)
        keyboard.send("ctrl+v")
        close_all_widgets()

    def simulate_typing(self):
        keyboard.write(self.text)
        close_all_widgets()

    def pin_group(self):
        self.parent_widget.pin_group()
        self.is_pinned = self.parent_widget.is_pinned
        self.btn_pin.setProperty("pinned", "true" if self.is_pinned else "false")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)
        reset_global_timer()


class RoundedWidget(QWidget):
    def __init__(self, sentence_group, parent=None, group="unpinned", index=0):
        super().__init__(parent)
        self.sentence_group = sentence_group
        self.group = group
        self.index = index

        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.create_text_line('simplified', '简：')
        self.create_text_line('traditional', '繁：')
        self.create_text_line('english', 'E：')

        self.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(246, 178, 107, 200);
                background-color: rgba(255, 204, 51, 200);
                padding: 0px;
                margin: 0px;
                font-size: 12px;
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

        self.adjustSize()

    def create_text_line(self, key, title):
        text = self.sentence_group.get(key, '').strip()
        if not text:
            return
        line_widget = TextLineWidget(text, title, self.is_pinned, self)
        self.main_layout.addWidget(line_widget)

    def _calc_background_size(self):
        content_height = self.main_layout.sizeHint().height()
        padding_y = 10
        bg_height = content_height + padding_y
        bg_width = 420
        return bg_width, bg_height

    def sizeHint(self):
        bg_width, bg_height = self._calc_background_size()
        return QSize(bg_width, bg_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_width, bg_height = self._calc_background_size()
        border_radius = 8

        if self.height() != bg_height:
            self.setFixedHeight(bg_height)
        if self.width() != bg_width:
            self.setFixedWidth(bg_width)

        if self.group == "pinned":
            bg_color, border_color = PINNED_COLORS[self.index % 2]
        else:
            bg_color, border_color = UNPINNED_COLORS[self.index % 2]

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)

        pen = QPen(border_color)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, bg_width - 2, bg_height - 2, border_radius, border_radius)

        super().paintEvent(event)

    def pin_group(self):
        pin_sentence_group(self.sentence_group)
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)
        for line_widget in self.findChildren(TextLineWidget):
            line_widget.is_pinned = self.is_pinned
            line_widget.btn_pin.setProperty("pinned", "true" if self.is_pinned else "false")
            line_widget.btn_pin.style().unpolish(line_widget.btn_pin)
            line_widget.btn_pin.style().polish(line_widget.btn_pin)
        reset_global_timer()

    def enterEvent(self, event):
        global mouse_hover_count, global_timer
        if not self.underMouse():
            return
        mouse_hover_count += 1
        if global_timer is not None and global_timer.isActive():
            global_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        QTimer.singleShot(50, self._delayed_leave_check)
        super().leaveEvent(event)

    def _delayed_leave_check(self):
        global mouse_hover_count
        if not self.underMouse():
            mouse_hover_count -= 1
            if mouse_hover_count < 0:
                mouse_hover_count = 0
            if mouse_hover_count == 0:
                reset_global_timer()


def show_widgets():
    global active_widgets, mouse_hover_count
    base_x, base_y = 100, 100
    current_y = base_y
    spacing = 15

    if active_widgets:
        close_all_widgets()
        return

    mouse_hover_count = 0
    if global_timer is not None and global_timer.isActive():
        global_timer.stop()

    for i, group in enumerate(pinned_groups):
        w = RoundedWidget(group, group="pinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing

    for i, group in enumerate(unpinned_groups):
        w = RoundedWidget(group, group="unpinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing


# -------------------模擬數據與按鍵-------------------
counter = 1
def simulate_new_group():
    global counter
    new_group = {
        'simplified': f"简体示例 {counter}：你们好吗？山上的小朋友",
        'traditional': f"繁體示例 {counter}：你們好嗎？山上的小朋友",
        'english': f"Example {counter}：How are you? The kids on the hill."
    }
    add_sentence_group(new_group)  # 添加时会自动经过审查
    print(f"尝试新增组 {counter}")
    counter += 1
    if active_widgets:
        close_all_widgets()
        show_widgets()

class KeyboardThread(QThread):
    trigger = Signal()
    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()
        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()

if __name__ == "__main__":
    # 启动时先加载审查文件和钉住记录
    load_reviewed_lines()
    load_pinned()

    # 测试数据（若其中有行在reviewed_lines.txt中，则不会被添加）
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
        },
        {
            'simplified': "",
            'traditional': "",
            'english': "yeah"
        }
    ]
    for group in test_groups:
        add_sentence_group(group)  # 测试组也会经过审查

    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widgets)
    kb_thread.start()

    # 可选：定时新增测试组
    # timer = QTimer()
    # timer.timeout.connect(simulate_new_group)
    # timer.start(8000)

    sys.exit(app.exec())