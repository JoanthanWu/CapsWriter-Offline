import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                               QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout, QFont
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize

MAX_TOTAL = 12  # 最大显示组数
pinned_groups = []  # 存储钉住的组 {'simplified': '', 'traditional': '', 'english': ''}
unpinned_groups = []  # 存储未钉住的组
active_widgets = []
global_timer = None
PINNED_FILE = "pinned_groups.json"  # 更改文件名避免冲突

# 颜色配置保持不变
PINNED_COLORS = [
    (QColor(155, 68, 0, 255), QColor(37, 73, 78)),  # #9B4400背景 / #25494E边框
    (QColor(179, 92, 68, 255), QColor(46, 107, 117)),  # #B35C44背景 / #2e6b75边框
]

UNPINNED_COLORS = [
    (QColor(44, 79, 84, 255), QColor(137, 103, 71)),  # 高麗納戸色#2C4F54背景 / 896747边框
    (QColor(31, 49, 52, 255), QColor(84, 67, 50)),  # 百入茶色#1F3134背景 / 544332边框
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
    """重置全局倒計時，時間到後關閉所有 widget"""
    global global_timer
    if global_timer is None:
        global_timer = QTimer()
        global_timer.setSingleShot(True)
        global_timer.timeout.connect(close_all_widgets)
    global_timer.start(5000)  # 5 秒


# -------------------核心邏輯-------------------
def group_equal(group1, group2):
    """判断两组数据是否相等（忽略空值顺序）"""
    if not isinstance(group1, dict) or not isinstance(group2, dict):
        return False
    # 比较所有非空字段
    keys = {'simplified', 'traditional', 'english'}
    for key in keys:
        val1 = group1.get(key, '').strip()
        val2 = group2.get(key, '').strip()
        if val1 != val2:
            return False
    return True


def add_sentence_group(new_group):
    """添加新的文字组（包含简、繁、英）"""
    global unpinned_groups
    # 检查是否已在钉住组中
    for pg in pinned_groups:
        if group_equal(pg, new_group):
            return
    # 检查是否已在未钉住组中
    for ug in unpinned_groups:
        if group_equal(ug, new_group):
            return
    # 添加到未钉住组
    unpinned_groups.append(new_group)
    # 维持最大数量
    max_unpinned = MAX_TOTAL - len(pinned_groups)
    while len(unpinned_groups) > max_unpinned:
        removed = unpinned_groups.pop(0)
        print("移除最舊未釘住组")


def pin_sentence_group(group):
    """钉住/取消钉住一组文字"""
    global pinned_groups, unpinned_groups
    # 检查是否已在钉住组
    for i, pg in enumerate(pinned_groups):
        if group_equal(pg, group):
            # 取消钉住，移到未钉住组
            pinned_groups.pop(i)
            add_sentence_group(group)
            print("取消釘住组")
            save_pinned()
            return
    # 不在钉住组，添加到钉住组
    pinned_groups.append(group)
    # 从非钉住组移除
    for i, ug in enumerate(unpinned_groups):
        if group_equal(ug, group):
            unpinned_groups.pop(i)
            break
    # 维持最大数量
    max_unpinned = MAX_TOTAL - len(pinned_groups)
    while len(unpinned_groups) > max_unpinned:
        unpinned_groups.pop(0)
    print("已釘住组")
    save_pinned()


def get_all_groups():
    return pinned_groups + unpinned_groups


class MultiLineElidedLabel(QLabel):
    """多行文本省略标签（保持原有功能）"""

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
        self.sentence_group = sentence_group  # 文字组 {'simplified': '', 'traditional': '', 'english': ''}
        self.group = group  # "pinned" 或 "unpinned"
        self.index = index  # 在該組內的順序

        # 创建文本显示区域（垂直布局）
        self.text_container = QWidget(self)
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setSpacing(2)  # 文字间间距
        self.text_layout.setContentsMargins(0, 0, 0, 0)

        # 存储三个文本标签的引用
        self.labels = {}
        fixed_width = 300
        font = QFont()
        font.setPointSize(12)

        # 添加三种文字标签（只显示有内容的）
        for key, label_text in [
            ('simplified', '简体：'),
            ('traditional', '繁体：'),
            ('english', 'English：')
        ]:
            text = self.sentence_group.get(key, '').strip()
            if text:  # 只显示非空内容
                # 创建标签容器（标题+内容）
                line_widget = QWidget()
                line_layout = QHBoxLayout(line_widget)
                line_layout.setSpacing(5)
                line_layout.setContentsMargins(0, 0, 0, 0)

                # 标题标签（如"简体："）
                title_label = QLabel(label_text)
                title_label.setFont(font)
                title_label.setStyleSheet("color: #ffffcc;")  # 浅色标题
                title_label.setFixedWidth(60)  # 固定标题宽度

                # 内容标签
                content_label = MultiLineElidedLabel(
                    text,
                    max_lines=2,
                    fixed_width=fixed_width - 70,  # 减去标题和间距
                    ellipsis="[...]"
                )
                content_label.setFont(font)
                content_label.setStyleSheet("color: white;")
                content_label.setText(text)  # 触发高度计算

                line_layout.addWidget(title_label)
                line_layout.addWidget(content_label)
                self.text_layout.addWidget(line_widget)
                self.labels[key] = content_label

        # 如果没有内容，显示占位符
        if not self.labels:
            empty_label = QLabel("无内容")
            empty_label.setFont(font)
            empty_label.setStyleSheet("color: white;")
            self.text_layout.addWidget(empty_label)
            self.labels['empty'] = empty_label

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
        self.btn_pin.clicked.connect(self.pin_group)
        self.btn_copy.clicked.connect(self.copy_only)
        self.btn_paste.clicked.connect(self.copy_and_paste)
        self.btn_type.clicked.connect(self.simulate_typing)

        self.buttons_container.hide()

        # 主 layout
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.text_container)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # 套用樣式表（保持不变）
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

        # 初始化 pinned 屬性
        is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)
        self.btn_pin.setProperty("pinned", "true" if is_pinned else "false")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)

        self.adjustSize()

    def _calc_background_size(self):
        """计算背景大小"""
        # 文本容器总高度 + 内边距
        text_height = self.text_container.height()
        padding_y = 8  # 上下内边距总和
        bg_height = text_height + padding_y

        # 宽度固定（可根据需要调整）
        bg_width = 320
        return bg_width, bg_height

    def sizeHint(self):
        bg_width, bg_height = self._calc_background_size()
        return QSize(bg_width, bg_height)

    def resizeEvent(self, event):
        """按鈕容器固定在左上角"""
        super().resizeEvent(event)
        self.buttons_container.move(5, 5)  # 固定位置

    def enterEvent(self, event):
        """滑鼠進入 → 顯示按鈕"""
        self.buttons_container.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """滑鼠離開 → 隱藏按鈕"""
        self.buttons_container.hide()
        super().leaveEvent(event)

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

    def _get_combined_text(self, separator="\n\n"):
        """组合三种文字为字符串"""
        parts = []
        if self.sentence_group.get('simplified'):
            parts.append(f"简体：{self.sentence_group['simplified']}")
        if self.sentence_group.get('traditional'):
            parts.append(f"繁体：{self.sentence_group['traditional']}")
        if self.sentence_group.get('english'):
            parts.append(f"English：{self.sentence_group['english']}")
        return separator.join(parts)

    def copy_only(self):
        """复制组合文本"""
        text = self._get_combined_text()
        QApplication.clipboard().setText(text)
        print("已複製组内容")
        reset_global_timer()

    def copy_and_paste(self):
        """复制并粘贴（默认粘贴简体，如果没有则按顺序选第一个有内容的）"""
        # 优先粘贴简体
        text_to_paste = self.sentence_group.get('simplified') or \
                        self.sentence_group.get('traditional') or \
                        self.sentence_group.get('english') or ""

        QApplication.clipboard().setText(text_to_paste)
        time.sleep(0.1)
        keyboard.send("ctrl+v")
        close_all_widgets()

    def simulate_typing(self):
        """模拟输入（默认输入简体，如果没有则按顺序选第一个有内容的）"""
        text_to_type = self.sentence_group.get('simplified') or \
                       self.sentence_group.get('traditional') or \
                       self.sentence_group.get('english') or ""
        keyboard.write(text_to_type)
        close_all_widgets()

    def pin_group(self):
        """钉住/取消钉住当前组"""
        pin_sentence_group(self.sentence_group)
        is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)
        self.btn_pin.setProperty("pinned", "true" if is_pinned else "false")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)
        reset_global_timer()


def show_widgets():
    global active_widgets
    base_x, base_y = 100, 100
    current_y = base_y
    spacing = 10  # 组之间的间距

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
    # 模拟一组包含三种文字的数据
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

    # 初始化测试数据（包含三种文字的组）
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
            'simplified': "简繁混合示例",
            'traditional': "簡繁混合示例",
            'english': ""
        }
    ]
    for group in test_groups:
        add_sentence_group(group)

    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widgets)
    kb_thread.start()

    # 模拟定时新增组（注释掉可关闭）
    # timer = QTimer()
    # timer.timeout.connect(simulate_new_group)
    # timer.start(8000)

    sys.exit(app.exec())