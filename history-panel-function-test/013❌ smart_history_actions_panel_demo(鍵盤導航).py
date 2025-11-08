import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QHBoxLayout, QVBoxLayout)
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout, QFont
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize, QEvent

# 审查文件配置
REVIEW_FILE = "reviewed_lines.txt"
reviewed_lines = set()  # 存储审查文件中的所有行（去重）


MAX_TOTAL = 12
pinned_groups = []
unpinned_groups = []
active_widgets = []  # 存储当前显示的所有句子组窗口
global_timer = None
PINNED_FILE = "pinned_groups.json"

# 跟踪鼠标在任意widget区域的数量
mouse_hover_count = 0

# 键盘导航核心变量（全局跟踪选择状态）
current_group_idx = 0    # 当前选中的句子组索引（0-based）
current_line_idx = 0     # 当前选中的文本行索引（0:简体, 1:繁体, 2:英文）
current_btn_idx = 0      # 当前选中的按钮索引
BUTTON_ORDER = ["btn_pin", "btn_copy", "btn_paste", "btn_type", "btn_review"]  # 按钮顺序


# 颜色配置（正常/选中状态区分）
PINNED_COLORS = [
    (QColor(155, 68, 0, 255), QColor(37, 73, 78)),
    (QColor(179, 92, 68, 255), QColor(46, 107, 117)),
]
UNPINNED_COLORS = [
    (QColor(44, 79, 84,255), QColor(137, 103, 71)),
    (QColor(31, 49, 52,255), QColor(84, 67, 50)),
]
SELECTED_PINNED_COLORS = [
    (QColor(200, 100, 50, 255), QColor(255, 255, 153, 255)),  # 选中状态颜色（更亮）
    (QColor(220, 120, 80, 255), QColor(255, 255, 153, 255)),
]
SELECTED_UNPINNED_COLORS = [
    (QColor(60, 100, 110,255), QColor(255, 255, 153, 255)),
    (QColor(45, 70, 75,255), QColor(255, 255, 153, 255)),
]
SELECTED_LINE_COLOR = "background-color: rgba(255, 255, 100, 50);"  # 选中行的背景色


# 读取审查文件
def load_reviewed_lines():
    global reviewed_lines
    reviewed_lines = set()
    if not os.path.exists(REVIEW_FILE):
        with open(REVIEW_FILE, "w", encoding="utf-8") as f:
            pass
        return
    try:
        with open(REVIEW_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    reviewed_lines.add(line)
        print(f"已加载审查文件，共 {len(reviewed_lines)} 条记录")
    except Exception as e:
        print(f"读取审查文件失败：{e}")


# 储存 / 读取 pinned
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


# 核心逻辑：窗口管理
def close_all_widgets():
    global active_widgets, current_group_idx, current_line_idx, current_btn_idx
    for w in active_widgets[:]:
        w.close()
    active_widgets.clear()
    # 重置选择状态
    current_group_idx = 0
    current_line_idx = 0
    current_btn_idx = 0


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

def add_sentence_group(new_group):
    global unpinned_groups
    for key in ['simplified', 'traditional', 'english']:
        text = new_group.get(key, '').strip()
        if text and text in reviewed_lines:
            print(f"审查拦截：'{text}' 已在审查列表中，不添加")
            return
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


class TextLineWidget(QWidget):
    def __init__(self, text, title, is_pinned, is_reviewing, line_idx, parent=None):
        super().__init__(parent)
        self.text = text
        self.parent_widget = parent  # 关联的RoundedWidget
        self.is_pinned = is_pinned
        self.is_reviewing = is_reviewing
        self.line_idx = line_idx  # 文本行索引（0:简体, 1:繁体, 2:英文）
        self.buttons = {}  # 存储按钮引用
        self.is_selected = False  # 是否被选中

        self.line_layout = QHBoxLayout(self)
        self.line_layout.setSpacing(5)
        self.line_layout.setContentsMargins(0, 0, 0, 0)

        # 标题标签
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("SimHei", 12))
        self.title_label.setStyleSheet("color: #ffffcc;")
        self.line_layout.addWidget(self.title_label)

        # 文本标签
        self.content_label = MultiLineElidedLabel(
            text, max_lines=2, fixed_width=200, ellipsis="[...]"
        )
        self.content_label.setFont(QFont("SimHei", 12))
        self.content_label.setStyleSheet("color: white;")
        self.content_label.setText(text)
        self.line_layout.addWidget(self.content_label)

        # 按钮容器（始终显示，方便键盘选择）
        self.buttons_container = QWidget(self)
        self.buttons_container.setStyleSheet("")
        self.buttons_container.show()

        # 按钮布局
        btn_layout = QHBoxLayout(self.buttons_container)
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # 创建按钮并存储引用
        self.btn_pin = QPushButton("📌")
        self.btn_copy = QPushButton("📑")
        self.btn_paste = QPushButton("📋")
        self.btn_type = QPushButton("✍️")
        self.btn_review = QPushButton("⛓")
        self.buttons = {
            "btn_pin": self.btn_pin,
            "btn_copy": self.btn_copy,
            "btn_paste": self.btn_paste,
            "btn_type": self.btn_type,
            "btn_review": self.btn_review
        }

        # 设置按钮ID和初始样式
        for name, btn in self.buttons.items():
            btn.setObjectName(name)
        self.btn_pin.setProperty("pinned", "true" if self.is_pinned else "false")
        self.btn_review.setProperty("reviewing", "true" if self.is_reviewing else "false")
        self._update_btn_styles()

        # 绑定按钮事件
        self.btn_pin.clicked.connect(self.pin_group)
        self.btn_copy.clicked.connect(self.copy_only)
        self.btn_paste.clicked.connect(self.copy_and_paste)
        self.btn_type.clicked.connect(self.simulate_typing)
        self.btn_review.clicked.connect(self.toggle_review)

        # 设置按钮大小
        for btn in self.buttons.values():
            btn.setFixedSize(24, 20)
            btn_layout.addWidget(btn)

        self.buttons_container.raise_()

    def _update_btn_styles(self):
        """更新按钮样式（解决样式未生效问题）"""
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)
        self.btn_review.style().unpolish(self.btn_review)
        self.btn_review.style().polish(self.btn_review)

    def set_selected(self, selected, btn_idx=0):
        """设置当前行是否被选中，并高亮对应按钮"""
        self.is_selected = selected
        # 行背景高亮
        self.setStyleSheet(SELECTED_LINE_COLOR if selected else "")
        # 按钮高亮
        for i, btn_name in enumerate(BUTTON_ORDER):
            btn = self.buttons.get(btn_name)
            if btn:
                # 选中按钮加黄色边框，未选中则清除
                btn.setStyleSheet("border: 2px solid yellow;" if i == btn_idx else "")
        self.update()

    def trigger_button(self, btn_idx):
        """触发指定索引的按钮功能"""
        if 0 <= btn_idx < len(BUTTON_ORDER):
            btn_name = BUTTON_ORDER[btn_idx]
            if btn_name == "btn_pin":
                self.pin_group()
            elif btn_name == "btn_copy":
                self.copy_only()
            elif btn_name == "btn_paste":
                self.copy_and_paste()
            elif btn_name == "btn_type":
                self.simulate_typing()
            elif btn_name == "btn_review":
                self.toggle_review()

    # 按钮功能实现
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
        self._update_btn_styles()
        reset_global_timer()

    def toggle_review(self):
        line = self.text.strip()
        if not line:
            return
        lines = [l.strip() for l in open(REVIEW_FILE, "r", encoding="utf-8").readlines() if l.strip()] if os.path.exists(REVIEW_FILE) else []
        if line in lines:
            lines.remove(line)
            self.is_reviewing = False
            print(f"已從審查清單刪除: {line[:20]}...")
        else:
            lines.append(line)
            self.is_reviewing = True
            print(f"已加入審查清單: {line[:20]}...")
        with open(REVIEW_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        load_reviewed_lines()
        self.btn_review.setProperty("reviewing", "true" if self.is_reviewing else "false")
        self._update_btn_styles()
        reset_global_timer()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        label_pos = self.content_label.pos()
        self.buttons_container.move(label_pos.x(), label_pos.y())
        self.buttons_container.setFixedSize(self.buttons_container.sizeHint())


class RoundedWidget(QWidget):
    def __init__(self, sentence_group, parent=None, group="unpinned", index=0):
        super().__init__(parent)
        self.sentence_group = sentence_group
        self.group = group  # "pinned"或"unpinned"
        self.index = index  # 组在列表中的索引
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)
        self.text_lines = []  # 存储当前组的所有文本行（TextLineWidget）
        self.is_selected = False  # 当前组是否被选中

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建文本行（简体/繁体/英文）
        self.create_text_line('simplified', '简：', 0)  # line_idx=0
        self.create_text_line('traditional', '繁：', 1)  # line_idx=1
        self.create_text_line('english', '译：', 2)      # line_idx=2

        # 样式表
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
            QPushButton#btn_copy { border-radius: 0; border-right: none; }
            QPushButton#btn_paste { border-radius: 0; border-right: none; }
            QPushButton#btn_type {
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            QPushButton#btn_review {
                width: 16px; height: 16px; min-width: 16px; min-height: 16px;
                max-width: 16px; max-height: 16px; border-radius: 9px;
                font-size: 12px; padding: 0px; margin: 0px;
            }
            QPushButton#btn_pin[pinned="true"] { background-color: rgba(120, 63, 4, 250); }
            QPushButton#btn_pin[pinned="false"] { background-color: rgba(255, 204, 51, 200); }
            QPushButton#btn_review[reviewing="true"] { background-color: rgba(120, 63, 4, 250); }
            QPushButton#btn_review[reviewing="false"] { background-color: rgba(255, 204, 51, 200); }
            QPushButton:hover { background-color: rgba(255, 255, 153, 200); }
            QPushButton#btn_pin[pinned="true"]:hover { background-color: rgba(255, 255, 153, 200); }
            QPushButton#btn_pin[pinned="false"]:hover { background-color: rgba(200,50,50,250); }
            QPushButton#btn_review[reviewing="true"]:hover { background-color: rgba(255, 255, 153, 200); }
            QPushButton#btn_review[reviewing="false"]:hover { background-color: rgba(200,50,50,250); }
        """)

        self.adjustSize()
        self.setFocusPolicy(Qt.StrongFocus)  # 确保能接收焦点

    def create_text_line(self, key, title, line_idx):
        text = self.sentence_group.get(key, '').strip()
        if not text:
            return
        is_reviewing = text in reviewed_lines
        line_widget = TextLineWidget(text, title, self.is_pinned, is_reviewing, line_idx, self)
        self.main_layout.addWidget(line_widget)
        self.text_lines.append(line_widget)

    def _calc_background_size(self):
        content_height = self.main_layout.sizeHint().height()
        padding_y = 10
        return 420, content_height + padding_y  # (width, height)

    def sizeHint(self):
        return QSize(*self._calc_background_size())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_width, bg_height = self._calc_background_size()
        border_radius = 8

        # 调整窗口大小
        if self.height() != bg_height:
            self.setFixedHeight(bg_height)
        if self.width() != bg_width:
            self.setFixedWidth(bg_width)

        # 选择背景色（根据选中状态）
        if self.is_selected:
            bg_color, border_color = (SELECTED_PINNED_COLORS if self.group == "pinned" else SELECTED_UNPINNED_COLORS)[self.index % 2]
        else:
            bg_color, border_color = (PINNED_COLORS if self.group == "pinned" else UNPINNED_COLORS)[self.index % 2]

        # 绘制背景和边框
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)
        painter.setPen(QPen(border_color, 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, bg_width-2, bg_height-2, border_radius, border_radius)

        # 选中组显示箭头标记
        if self.is_selected:
            painter.setPen(QPen(QColor(255, 255, 0), 2))  # 黄色箭头
            painter.drawText(5, 15, "▶")

        super().paintEvent(event)

    def set_selected(self, selected, line_idx=0, btn_idx=0):
        """设置当前组是否被选中，并同步更新文本行和按钮的选中状态"""
        self.is_selected = selected
        # 更新所有文本行的选中状态（只有指定行被选中）
        for line in self.text_lines:
            line.set_selected(selected and line.line_idx == line_idx, btn_idx if line.line_idx == line_idx else -1)
        self.update()  # 重绘
        if selected:
            self.setFocus()  # 强制获取焦点

    def pin_group(self):
        pin_sentence_group(self.sentence_group)
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)
        for line in self.text_lines:
            line.is_pinned = self.is_pinned
            line.btn_pin.setProperty("pinned", "true" if self.is_pinned else "false")
            line._update_btn_styles()
        reset_global_timer()


class KeyboardHandler(QWidget):
    """全局键盘事件处理器，确保所有按键都能被捕获"""
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.app.installEventFilter(self)  # 安装事件过滤器

    def eventFilter(self, obj, event):
        """过滤并处理键盘事件"""
        global current_group_idx, current_line_idx, current_btn_idx, active_widgets

        # 只处理键盘按下事件，且当前有显示的窗口
        if event.type() == QEvent.KeyPress and active_widgets:
            key = event.key()
            group_count = len(active_widgets)
            current_group = active_widgets[current_group_idx]
            line_count = len(current_group.text_lines)  # 当前组的有效文本行数

            # 上键：切换到上一个句子组
            if key == Qt.Key_Up:
                current_group_idx = (current_group_idx - 1) % group_count
                self._update_selection()
                return True  # 拦截事件，避免传递给其他组件

            # 下键：切换到下一个句子组
            elif key == Qt.Key_Down:
                current_group_idx = (current_group_idx + 1) % group_count
                self._update_selection()
                return True

            # 左键：切换到上一个按钮
            elif key == Qt.Key_Left:
                current_btn_idx = (current_btn_idx - 1) % len(BUTTON_ORDER)
                self._update_selection()
                return True

            # 右键：切换到下一个按钮
            elif key == Qt.Key_Right:
                current_btn_idx = (current_btn_idx + 1) % len(BUTTON_ORDER)
                self._update_selection()
                return True

            # 左Ctrl键：切换到上一个文本行（简体→繁体→英文）
            elif key == Qt.Key_Control and event.modifiers() == Qt.ControlModifier:
                if line_count > 0:
                    current_line_idx = (current_line_idx - 1) % line_count
                    self._update_selection()
                return True

            # 右Ctrl键：切换到下一个文本行
            elif key == Qt.Key_Control and event.modifiers() == Qt.RightModifier:
                if line_count > 0:
                    current_line_idx = (current_line_idx + 1) % line_count
                    self._update_selection()
                return True

            # 回车键：触发当前选中的按钮功能
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                if line_count > 0 and 0 <= current_line_idx < line_count:
                    current_line = current_group.text_lines[current_line_idx]
                    current_line.trigger_button(current_btn_idx)
                return True

        return super().eventFilter(obj, event)

    def _update_selection(self):
        """更新所有组的选中状态，确保只有当前组/行/按钮被高亮"""
        global current_group_idx, current_line_idx, current_btn_idx, active_widgets
        for i, group in enumerate(active_widgets):
            is_current_group = (i == current_group_idx)
            # 更新组的选中状态，同步当前行和按钮索引
            group.set_selected(is_current_group, current_line_idx if is_current_group else -1, current_btn_idx)


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

    # 显示所有句子组
    for i, group in enumerate(pinned_groups):
        w = RoundedWidget(group, group="pinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing

    for i, group in enumerate(unpinned_groups):
        w = RoundedWidget(group, group="unpinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing

    # 初始化选中状态（默认选中第一个组的第一行第一个按钮）
    if active_widgets:
        active_widgets[0].set_selected(True, 0, 0)


# 模拟数据与按键监听
counter = 1
def simulate_new_group():
    global counter
    new_group = {
        'simplified': f"简体示例 {counter}：你们好吗？山上的小朋友",
        'traditional': f"繁體示例 {counter}：你們好嗎？山上的小朋友",
        'english': f"Example {counter}：How are you? The kids on the hill."
    }
    add_sentence_group(new_group)
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
        keyboard.hook_key("z", handler, suppress=True)  # 按z键唤起widget
        keyboard.wait()

if __name__ == "__main__":
    load_reviewed_lines()
    load_pinned()

    # 测试数据
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
        add_sentence_group(group)

    app = QApplication(sys.argv)
    keyboard_handler = KeyboardHandler(app)  # 注册全局键盘事件处理器
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widgets)
    kb_thread.start()

    sys.exit(app.exec())