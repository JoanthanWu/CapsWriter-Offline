import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                               QHBoxLayout, QVBoxLayout, QFrame, QTextEdit, QDialog)
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout, QFont, QGuiApplication
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
import tomllib

# 配置文件路径
CONFIG_FILE = "history_panel_config.toml"

DEFAULT_CONFIG = {
    # 文本行定义（可自定义顺序、标题、键）
    "text_lines": [
        {"key": "simplified", "title": "简"},  # 简体
        {"key": "traditional", "title": "繁"},  # 繁体
        {"key": "english", "title": "译"}  # 英文
    ],
    # 标题文本配置
    "title": {
        "font_family": "Microsoft YaHei",
        "font_size": 9,
        "font_bold": True,
        "font_italic": False,
        "color": [252, 220, 129, 255],
        "bg_color": [0, 0, 0, 0],
        "hover_bg_color": [255, 240, 160, 140],
        "border_color": [0, 0, 0, 0],
        "border_width": 0,
        "min_width": 18,
        "max_width": 28,
        "padding": 1
    },
    # 内容文本配置
    "content": {
        "font_family": "Microsoft YaHei",
        "font_size": 9,
        "font_bold": False,
        "font_italic": False,
        "color": [255, 255, 255, 255],
        "bg_color": [0, 0, 0, 0],
        "hover_bg_color": [80, 0, 22, 50],
        "border_color": [0, 0, 0, 0],
        "border_width": 0,
        "line_spacing": 3,
        "max_lines": 2,
        "width": 320,
        "ellipsis": "[...]",
        "margins": [0, 0, 0, 0]
    },
    # 容器布局配置
    "widget": {
        "padding": [3, 3, 3, 3],
        "spacing": 5,
        "width": 350,
        "initial_x": 100,
        "initial_y": 100,
        "border_radius": 8,
        "border_width": 4
    },
    # 固定组颜色配置
    "pinned": {
        "bg_colors": [
            [155, 68, 0, 255],
            [179, 92, 68, 255]
        ],
        "border_colors": [
            [84, 67, 50, 255],
            [137, 103, 71, 255]
        ]
    },
    # 非固定组颜色配置
    "unpinned": {
        "bg_colors": [
            [44, 79, 84, 255],
            [31, 49, 52, 255]
        ],
        "border_colors": [
            [137, 103, 71, 255],
            [84, 67, 50, 255]
        ]
    },
    # 按钮配置
    "button": {
        "size": [24, 20],
        "normal_color": [255, 204, 51, 255],
        "hover_color": [255, 255, 153, 255],
        "pinned_color": [200, 50, 50, 255],
        "pinned_hover_color": [166, 0, 0, 255],
        "review_color": [200, 50, 50, 255],
        "review_hover_color": [166, 0, 0, 255],
        "border_radius": 10,
        "show_pin": True,
        "show_copy": True,
        "show_paste": True,
        "show_type": True,
        "show_edit": True,
        "show_review": True
    },
    # 全局行为配置
    "global": {
        "max_text_groups": 12,
        "auto_close_timeout": 10000,  # 延长超时时间便于测试
        "window_stay_on_top": True,
        "window_frameless": True,
        "history_panel_arrange_method": 1
    }
}


# 颜色转换辅助函数（列表转QColor和CSS格式）
def to_qcolor(color_list):
    """将[r, g, b, a]列表转换为QColor"""
    return QColor(*color_list)


def to_css_rgba(color_list):
    """直接使用 0-255 的 alpha 值（符合 Qt 兼容的格式）"""
    try:
        if not isinstance(color_list, list):
            color_list = [255, 255, 204, 255]

        r = max(0, min(255, int(color_list[0]))) if len(color_list) > 0 else 255
        g = max(0, min(255, int(color_list[1]))) if len(color_list) > 1 else 255
        b = max(0, min(255, int(color_list[2]))) if len(color_list) > 2 else 204
        a = max(0, min(255, int(color_list[3]))) if len(color_list) > 3 else 255

        return f"rgba({r}, {g}, {b}, {a})"
    except Exception as e:
        print(f"颜色解析错误：{e}，使用默认色")
        return "rgba(255, 255, 204, 255)"


# 读取配置文件（不存在或无效时生成默认配置）
def load_config():
    file_exists = os.path.exists(CONFIG_FILE)
    file_valid = False

    if file_exists and os.path.getsize(CONFIG_FILE) > 0:
        try:
            with open(CONFIG_FILE, "rb") as f:
                tomllib.load(f)
            file_valid = True
        except Exception as e:
            print(f"配置文件错误，重新生成：{e}")

    if not file_exists or not file_valid:
        try:
            if file_exists:
                os.remove(CONFIG_FILE)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                import toml
                f.write(toml.dumps(DEFAULT_CONFIG))
            print(f"生成默认配置：{CONFIG_FILE}")
        except Exception as e:
            print(f"生成配置失败，使用默认值：{e}")
            return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE, "rb") as f:
            panel_config = tomllib.load(f)
        return merge_configs(DEFAULT_CONFIG, panel_config)
    except Exception as e:
        print(f"读取配置失败，使用默认值：{e}")
        return DEFAULT_CONFIG


# 合并配置
def merge_configs(default, user):
    merged = default.copy()
    for key, value in user.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged


# 加载配置
panel_config = load_config()

# 审查文件配置
REVIEW_FILE = "history_sanitize_list.txt"
reviewed_lines = set()

# 全局参数
PINNED_FILE = "history_pinned_groups.json"
MAX_TEXT_GROUPS = panel_config["global"]["max_text_groups"]
pinned_groups = []
unpinned_groups = []
cached_widgets = []  # 缓存所有创建过的窗口实例（复用）
active_displayed_widgets = []  # 当前显示的窗口列表
global_timer = None
mouse_hover_count = 0
is_widgets_visible = False  # 新增：标记窗口是否处于显示状态


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
        print(f"加载审查记录：{len(reviewed_lines)}条")
    except Exception as e:
        print(f"读取审查文件失败：{e}")


# 储存/读取pinned
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


# 核心逻辑 - 隐藏所有窗口（替代关闭）
def hide_all_widgets():
    """隐藏所有缓存的窗口，不释放资源"""
    global active_displayed_widgets, mouse_hover_count, is_widgets_visible
    mouse_hover_count = 0
    for w in cached_widgets:
        w.hide()
    active_displayed_widgets.clear()
    is_widgets_visible = False  # 隐藏时同步更新状态标记


def reset_global_timer():
    global global_timer, mouse_hover_count
    if mouse_hover_count > 0:
        return
    if global_timer is None:
        global_timer = QTimer()
        global_timer.setSingleShot(True)
        global_timer.timeout.connect(hide_all_widgets)  # hide_all_widgets已同步状态
    if global_timer.isActive():
        global_timer.stop()
    global_timer.start(panel_config["global"]["auto_close_timeout"])


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
            print(f"审查拦截：'{text}'")
            return

    for pg in pinned_groups:
        if group_equal(pg, new_group):
            return
    for ug in unpinned_groups:
        if group_equal(ug, new_group):
            return

    unpinned_groups.append(new_group)
    max_unpinned = MAX_TEXT_GROUPS - len(pinned_groups)

    # ========== 关键修改开始 ==========
    # 1. 校验 max_unpinned 有效性，避免负数导致无限循环
    if max_unpinned < 0:
        unpinned_groups.clear()  # 固定组已超上限，清空所有非固定组
        print("固定组数量已达上限，清空所有非固定组")
        return

    # 2. 循环移除旧数据时，增加空列表判断
    while len(unpinned_groups) > max_unpinned:
        if not unpinned_groups:  # 空列表时直接退出循环
            break
        unpinned_groups.pop(0)
        print("移除最旧未钉住组")
    # ========== 关键修改结束 ==========


def pin_sentence_group(group):
    global pinned_groups, unpinned_groups
    for i, pg in enumerate(pinned_groups):
        if group_equal(pg, group):
            pinned_groups.pop(i)
            add_sentence_group(group)
            print("取消钉住组")
            save_pinned()
            return
    pinned_groups.append(group)
    for i, ug in enumerate(unpinned_groups):
        if group_equal(ug, group):
            unpinned_groups.pop(i)
            break
    max_unpinned = MAX_TEXT_GROUPS - len(pinned_groups)
    while len(unpinned_groups) > max_unpinned:
        unpinned_groups.pop(0)
    print("已钉住组")
    save_pinned()


class MultiLineElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.max_lines = panel_config["content"]["max_lines"]
        self.ellipsis = panel_config["content"]["ellipsis"]
        self.setWordWrap(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)

        font = QFont(
            panel_config["content"]["font_family"],
            panel_config["content"]["font_size"]
        )
        font.setBold(panel_config["content"]["font_bold"])
        font.setItalic(panel_config["content"]["font_italic"])
        self.setFont(font)

    def setText(self, text):
        fm = QFontMetrics(self.font())
        line_height = fm.lineSpacing() + panel_config["content"]["line_spacing"]

        if self.parent() and self.parent().width() > 0:
            parent_width = self.parent().width()
            title_width = self.parent().title_label.width()
            layout_width = parent_width - title_width - 20
        else:
            layout_width = panel_config["content"].get("width", 500)

        layout_width = max(layout_width, 100)

        layout = QTextLayout(text, self.font())
        layout.beginLayout()
        lines = []
        more_lines_exist = False
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(layout_width)
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
            while last_line and fm.horizontalAdvance(last_line + self.ellipsis) > layout_width:
                last_line = last_line[:-1]
            lines[-1] = last_line + self.ellipsis

        actual_lines = len(lines)
        self.setFixedHeight(actual_lines * line_height)
        super().setText("\n".join(lines))


class EditTextDialog(QDialog):
    def __init__(self, init_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑文字")
        self.init_text = init_text
        self.result_text = ""

        self.border_radius = panel_config["widget"]["border_radius"]
        self.bg_color = to_qcolor(panel_config["unpinned"]["bg_colors"][0])
        self.border_color = to_qcolor(panel_config["unpinned"]["border_colors"][0])
        self.font_family = panel_config["content"]["font_family"]
        self.font_size = panel_config["content"]["font_size"] + 3
        self.line_spacing = panel_config["content"]["line_spacing"] + 2

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_layout = QVBoxLayout(self)
        pad = panel_config["widget"]["padding"]
        main_layout.setContentsMargins(pad[0] + 1, pad[1] + 1, pad[2] + 1, pad[3] + 1)
        main_layout.setSpacing(panel_config["widget"]["spacing"])

        self.text_edit = QTextEdit()
        self.text_edit.setText(init_text)

        scroll_bar_style = f"""
            QScrollBar:vertical {{
                background-color: {to_css_rgba(panel_config["unpinned"]["bg_colors"][1])};
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {to_css_rgba(panel_config["button"]["hover_color"])};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {to_css_rgba(panel_config["button"]["normal_color"])};
            }}
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
                height: 0px;
                width: 0px;
            }}
            QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical {{
                background-color: {to_css_rgba(panel_config["unpinned"]["bg_colors"][0])};
                border-radius: 4px;
            }}
            QScrollBar:horizontal {{
                height: 0px;
            }}
        """

        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                font-family: {self.font_family};
                font-size: {self.font_size}px;
                line-height: {self.line_spacing}px;
                letter-spacing: 0.5px;
                color: {to_css_rgba(panel_config["content"]["color"])};
                background-color: {to_css_rgba(panel_config["unpinned"]["bg_colors"][1])};
                border: {panel_config["widget"]["border_width"] - 2}px solid {to_css_rgba(panel_config["unpinned"]["border_colors"][1])};
                border-radius: {self.border_radius - 2}px;
                padding: 2px;
            }}
            QTextEdit:focus {{
                border-color: {to_css_rgba(panel_config["button"]["hover_color"])};
                outline: none;
            }}
            {scroll_bar_style}
        """)

        edit_font = QFont(self.font_family, self.font_size)
        edit_font.setBold(panel_config["content"]["font_bold"])
        edit_font.setItalic(panel_config["content"]["font_italic"])
        self.text_edit.setFont(edit_font)

        self.text_edit.setMinimumSize(panel_config["widget"]["width"] - 20, 150)
        main_layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(3)
        btn_layout.setContentsMargins(0, 5, 0, 0)

        self.ok_btn = QPushButton("确认")
        self.ok_btn.setFixedSize(50, 30)
        self.ok_btn.clicked.connect(self.on_ok)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(50, 30)
        self.cancel_btn.clicked.connect(self.on_cancel)

        btn_style = f"""
            QPushButton {{
                font-family: {self.font_family};
                font-size: {self.font_size + 5}px;
                background-color: {to_css_rgba(panel_config["button"]["normal_color"])};
                border: 1px solid {to_css_rgba(panel_config["unpinned"]["border_colors"][0])};
                border-radius: {panel_config["button"]["border_radius"]}px;
                color: #000;
            }}
            QPushButton:hover {{
                background-color: {to_css_rgba(panel_config["button"]["hover_color"])};
            }}
            QPushButton:pressed {{
                background-color: {to_css_rgba(panel_config["button"]["pinned_color"])};
            }}
        """
        self.ok_btn.setStyleSheet(btn_style)
        self.cancel_btn.setStyleSheet(btn_style)

        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.adjustSize()
        if parent:
            self.move(parent.mapToGlobal(parent.rect().center()) - self.rect().center())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self.border_radius, self.border_radius)

        pen = QPen(self.border_color)
        pen.setWidth(panel_config["widget"]["border_width"])
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            self.rect().x() + 1, self.rect().y() + 1,
            self.rect().width() - 2, self.rect().height() - 2,
            self.border_radius - 1, self.border_radius - 1
        )

    def on_ok(self):
        self.result_text = self.text_edit.toPlainText().strip()
        if not self.result_text:
            return
        self.accept()

    def on_cancel(self):
        self.reject()

    def get_result(self):
        return self.result_text


class TextLineWidget(QWidget):
    def __init__(self, text, title, is_pinned, is_reviewing, parent=None):
        super().__init__(parent)
        self.text = text
        self.parent_widget = parent
        self.is_pinned = is_pinned
        self.is_reviewing = is_reviewing

        self.setStyleSheet("")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.line_layout = QHBoxLayout(self)
        self.line_layout.setSpacing(panel_config["content"]["line_spacing"])
        margins = panel_config["content"]["margins"]
        if not isinstance(margins, list) or len(margins) != 4:
            margins = [0, 0, 0, 0]
        left, top, right, bottom = margins
        self.line_layout.setContentsMargins(left, top, right, bottom)

        self.title_label = QLabel(title)
        font = QFont(
            panel_config["title"]["font_family"],
            panel_config["title"]["font_size"]
        )
        font.setBold(panel_config["title"]["font_bold"])
        font.setItalic(panel_config["title"]["font_italic"])
        self.title_label.setFont(font)

        self.title_label.setAttribute(Qt.WA_StyledBackground, True)
        self.title_original_style = (
            f"color: {to_css_rgba(panel_config['title']['color'])}; "
            f"background-color: {to_css_rgba(panel_config['title']['bg_color'])}; "
            f"border: {panel_config['title']['border_width']}px solid {to_css_rgba(panel_config['title']['border_color'])}; "
            f"padding: 0 {panel_config['title']['padding']}px; "
            f"border-radius: 4px;"
        )
        self.title_label.setStyleSheet(self.title_original_style)

        font_metrics = self.title_label.fontMetrics()
        text_width = font_metrics.horizontalAdvance(title)
        total_width = text_width + 2 * panel_config["title"]["padding"]
        min_width = panel_config["title"]["min_width"]
        max_width = panel_config["title"]["max_width"]
        final_width = max(min_width, min(total_width, max_width))
        self.title_label.setFixedWidth(final_width)

        self.content_label = MultiLineElidedLabel(text)
        self.content_label.setFont(QFont(
            panel_config["content"]["font_family"],
            panel_config["content"]["font_size"]
        ))

        self.content_label.setAttribute(Qt.WA_StyledBackground, True)
        self.content_original_style = (
            f"color: {to_css_rgba(panel_config['content']['color'])}; "
            f"background-color: {to_css_rgba(panel_config['content']['bg_color'])}; "
            f"border: {panel_config['content']['border_width']}px solid {to_css_rgba(panel_config['content']['border_color'])}; "
            f"border-radius: 4px;"
        )
        self.content_label.setStyleSheet(self.content_original_style)
        self.content_label.setText(text)

        self.line_layout.addWidget(self.title_label, stretch=0)
        self.line_layout.addWidget(self.content_label, stretch=1)

        self.buttons_container = QWidget(self)
        self.buttons_container.setAttribute(Qt.WA_TranslucentBackground)
        self.buttons_container.hide()

        btn_layout = QHBoxLayout(self.buttons_container)
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        button_order = ["pin", "edit", "copy", "paste", "type", "review"]
        self.buttons = {}
        for name in button_order:
            if panel_config["button"][f"show_{name}"]:
                if name == "pin":
                    self.buttons[name] = QPushButton("📌")
                elif name == "edit":
                    self.buttons[name] = QPushButton("✏️")
                elif name == "copy":
                    self.buttons[name] = QPushButton("📑")
                elif name == "paste":
                    self.buttons[name] = QPushButton("📋")
                elif name == "type":
                    self.buttons[name] = QPushButton("✍️")
                elif name == "review":
                    self.buttons[name] = QPushButton("⛓")

        for name, btn in self.buttons.items():
            btn.setObjectName(f"btn_{name}")
            if name == "pin":
                btn.setProperty("pinned", "true" if self.is_pinned else "false")
            if name == "review":
                btn.setProperty("reviewing", "true" if self.is_reviewing else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if "pin" in self.buttons:
            self.buttons["pin"].clicked.connect(self.pin_group)
        if "edit" in self.buttons:
            self.buttons["edit"].clicked.connect(self.edit_label_text)
        if "copy" in self.buttons:
            self.buttons["copy"].clicked.connect(self.copy_only)
        if "paste" in self.buttons:
            self.buttons["paste"].clicked.connect(self.copy_and_paste)
        if "type" in self.buttons:
            self.buttons["type"].clicked.connect(self.simulate_typing)
        if "review" in self.buttons:
            self.buttons["review"].clicked.connect(self.toggle_review)

        btn_w, btn_h = panel_config["button"]["size"]
        button_list = list(self.buttons.items())

        for i, (name, btn) in enumerate(button_list[:5]):
            btn.setFixedSize(btn_w, btn_h)
            btn_layout.addWidget(btn)

        if len(button_list) >= 6:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setFixedWidth(18)
            sep_color = to_css_rgba(panel_config['unpinned']['border_colors'][0])
            separator.setStyleSheet(f"border: 3px solid {sep_color}; background-color: transparent;")
            btn_layout.addWidget(separator)

            name, btn = button_list[5]
            btn.setFixedSize(btn_w, btn_h)
            btn_layout.addWidget(btn)

        self.buttons_container.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn_width = self.buttons_container.sizeHint().width()
        x = self.width() - btn_width - 5
        y = (self.height() - self.buttons_container.sizeHint().height()) // 2
        self.buttons_container.move(x, y)
        self.buttons_container.setFixedSize(self.buttons_container.sizeHint())

    def enterEvent(self, event):
        self.title_label.setStyleSheet(
            f"{self.title_original_style} background-color: {to_css_rgba(panel_config['title']['hover_bg_color'])};"
        )
        self.content_label.setStyleSheet(
            f"{self.content_original_style} background-color: {to_css_rgba(panel_config['content']['hover_bg_color'])};"
        )
        self.buttons_container.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.title_label.setStyleSheet(self.title_original_style)
        self.content_label.setStyleSheet(self.content_original_style)
        self.buttons_container.hide()
        super().leaveEvent(event)

    def copy_only(self):
        QApplication.clipboard().setText(self.text)
        print(f"已复制: {self.text[:20]}...")
        reset_global_timer()

    def copy_and_paste(self):
        QApplication.clipboard().setText(self.text)
        time.sleep(0.1)
        keyboard.send("ctrl+v")
        hide_all_widgets()

    def simulate_typing(self):
        keyboard.write(self.text)
        hide_all_widgets()

    def pin_group(self):
        self.parent_widget.pin_group()
        self.is_pinned = self.parent_widget.is_pinned
        if "pin" in self.buttons:
            self.buttons["pin"].setProperty("pinned", "true" if self.is_pinned else "false")
            self.buttons["pin"].style().unpolish(self.buttons["pin"])
            self.buttons["pin"].style().polish(self.buttons["pin"])
        reset_global_timer()

    def edit_label_text(self):
        old_text = self.text.strip()
        dialog = EditTextDialog(self.text, self)
        dialog.adjustSize()

        label_top_global = self.content_label.mapToGlobal(self.content_label.rect().topLeft())
        current_screen = QGuiApplication.screenAt(label_top_global)
        if not current_screen:
            current_screen = QGuiApplication.primaryScreen()
        screen_geo = current_screen.availableGeometry()
        screen_max_x = screen_geo.width()
        screen_max_y = screen_geo.height()
        screen_bottom = screen_geo.bottom()
        screen_left = screen_geo.left()
        screen_top = screen_geo.top()

        dialog_x = label_top_global.x() + (self.content_label.width() - dialog.width()) // 2
        dialog_y = label_top_global.y()

        if dialog_x + dialog.width() > screen_geo.right():
            dialog_x = screen_geo.right() - dialog.width() - 10
        if dialog_x < screen_left:
            dialog_x = screen_left + 10
        dialog_bottom = dialog_y + dialog.height()
        if dialog_bottom > screen_bottom:
            dialog_y = screen_bottom - dialog.height() - 10
            if dialog_y < screen_top:
                dialog_y = screen_top + 10

        dialog.move(dialog_x, dialog_y)

        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_result()
            self.text = new_text
            self.content_label.setText(new_text)

            if self.parent_widget and hasattr(self.parent_widget, 'sentence_group'):
                target_key = None
                for line_config in panel_config["text_lines"]:
                    key = line_config["key"]
                    if self.parent_widget.sentence_group.get(key, "").strip() == old_text:
                        target_key = key
                        break

                if target_key:
                    self.parent_widget.sentence_group[target_key] = new_text
                    global pinned_groups, unpinned_groups
                    for i, group in enumerate(pinned_groups):
                        if group_equal(group, self.parent_widget.sentence_group):
                            pinned_groups[i][target_key] = new_text
                            save_pinned()
                            break
                    for i, group in enumerate(unpinned_groups):
                        if group_equal(group, self.parent_widget.sentence_group):
                            unpinned_groups[i][target_key] = new_text
                            break

            reset_global_timer()

    def toggle_review(self):
        line = self.text.strip()
        if not line:
            return

        lines = []
        if os.path.exists(REVIEW_FILE):
            with open(REVIEW_FILE, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]

        if line in lines:
            lines.remove(line)
            self.is_reviewing = False
            print(f"移除审查：{line[:20]}...")
        else:
            lines.append(line)
            self.is_reviewing = True
            print(f"添加审查：{line[:20]}...")

        with open(REVIEW_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        load_reviewed_lines()

        if "review" in self.buttons:
            self.buttons["review"].setProperty("reviewing", "true" if self.is_reviewing else "false")
            self.buttons["review"].style().unpolish(self.buttons["review"])
            self.buttons["review"].style().polish(self.buttons["review"])

        reset_global_timer()


class RoundedWidget(QWidget):
    def __init__(self, sentence_group, parent=None, group="unpinned", index=0):
        super().__init__(parent)
        self.sentence_group = sentence_group
        self.group = group
        self.index = index
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)

        self.main_layout = QVBoxLayout(self)
        pad_top, pad_right, pad_bottom, pad_left = panel_config["widget"]["padding"]
        self.main_layout.setContentsMargins(pad_left, pad_top, pad_right, pad_bottom)
        self.main_layout.setSpacing(panel_config["content"]["line_spacing"])

        for line_config in panel_config["text_lines"]:
            key = line_config["key"]
            title = line_config["title"]
            self.create_text_line(key, title)

        self.setStyleSheet(self._get_stylesheet())
        self.setFixedWidth(panel_config["widget"]["width"])
        self.adjustSize()

    def update_group_data(self, sentence_group, group_type, index):
        """更新窗口数据，复用已有窗口实例"""
        self.sentence_group = sentence_group
        self.group = group_type
        self.index = index
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)

        # 清空原有文本行
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 重新创建文本行
        for line_config in panel_config["text_lines"]:
            key = line_config["key"]
            title = line_config["title"]
            self.create_text_line(key, title)

        # 更新样式和尺寸
        self.setStyleSheet(self._get_stylesheet())
        self.adjustSize()
        self.update()

    def _get_stylesheet(self):
        normal_color = to_css_rgba(panel_config['button']['normal_color'])
        hover_color = to_css_rgba(panel_config['button']['hover_color'])
        pinned_color = to_css_rgba(panel_config['button']['pinned_color'])
        pinned_hover_color = to_css_rgba(panel_config['button']['pinned_hover_color'])
        review_color = to_css_rgba(panel_config['button']['review_color'])
        review_hover_color = to_css_rgba(panel_config['button']['review_hover_color'])
        border_color = to_css_rgba(panel_config['unpinned']['border_colors'][0])

        return f"""
            QPushButton {{
                border: 1px solid {border_color};
                background-color: {normal_color};
                padding: 0px;
                margin: 0px;
                font-size: 12px;
            }}

            QPushButton#btn_pin {{
                border-top-left-radius: {panel_config['button']['border_radius']}px;
                border-bottom-left-radius: {panel_config['button']['border_radius']}px;
                border-right: none;
            }}
            QPushButton#btn_edit {{
                border-radius: 0;
                border-right: none;
            }}
            QPushButton#btn_copy {{
                border-radius: 0;
                border-right: none;
            }}
            QPushButton#btn_paste {{
                border-radius: 0;
                border-right: none;
            }}
            QPushButton#btn_type {{
                border-top-right-radius: {panel_config['button']['border_radius']}px;
                border-bottom-right-radius: {panel_config['button']['border_radius']}px;
                border-right: none;
            }}
            QPushButton#btn_review {{
                width: {panel_config['button']['size'][0]}px;
                height: {panel_config['button']['size'][1]}px;
                border-radius: {panel_config['button']['border_radius']}px;
                font-size: 14px;
            }}

            QPushButton#btn_pin[pinned="true"] {{
                background-color: {pinned_color};
            }}
            QPushButton#btn_pin[pinned="false"] {{
                background-color: {normal_color};
            }}

            QPushButton#btn_review[reviewing="true"] {{
                background-color: {review_color};
            }}
            QPushButton#btn_review[reviewing="false"] {{
                background-color: {normal_color};
            }}

            QPushButton#btn_pin[pinned="true"]:hover {{
                background-color: {pinned_hover_color};
            }}
            QPushButton#btn_pin[pinned="false"]:hover {{
                background-color: {hover_color};
            }}

            QPushButton#btn_review[reviewing="true"]:hover {{
                background-color: {review_hover_color};
            }}
            QPushButton#btn_review[reviewing="false"]:hover {{
                background-color: {hover_color};
            }}

            QPushButton#btn_edit:hover,
            QPushButton#btn_copy:hover,
            QPushButton#btn_paste:hover,
            QPushButton#btn_type:hover {{
                background-color: {hover_color};
            }}
        """

    def create_text_line(self, key, title):
        text = self.sentence_group.get(key, '').strip()
        if not text:
            return
        is_reviewing = text in reviewed_lines
        line_widget = TextLineWidget(text, title, self.is_pinned, is_reviewing, self)
        self.main_layout.addWidget(line_widget)

    def _calc_background_size(self):
        content_height = self.main_layout.sizeHint().height()
        pad_top, _, pad_bottom, _ = panel_config["widget"]["padding"]
        bg_height = content_height + pad_top + pad_bottom
        bg_width = panel_config["widget"]["width"]
        return bg_width, bg_height

    def sizeHint(self):
        bg_width, bg_height = self._calc_background_size()
        return QSize(bg_width, bg_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_width, bg_height = self._calc_background_size()
        border_radius = panel_config["widget"]["border_radius"]

        if self.height() != bg_height:
            self.setFixedHeight(bg_height)
        if self.width() != bg_width:
            self.setFixedWidth(bg_width)

        if self.group == "pinned":
            colors = panel_config["pinned"]["bg_colors"]
            border_colors = panel_config["pinned"]["border_colors"]
        else:
            colors = panel_config["unpinned"]["bg_colors"]
            border_colors = panel_config["unpinned"]["border_colors"]

        color_idx = self.index % len(colors)
        bg_color = to_qcolor(colors[color_idx])
        border_color = to_qcolor(border_colors[color_idx % len(border_colors)])

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)

        pen = QPen(border_color)
        pen.setWidth(panel_config["widget"]["border_width"])
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, bg_width - 2, bg_height - 2, border_radius, border_radius)

        super().paintEvent(event)

    def pin_group(self):
        pin_sentence_group(self.sentence_group)
        self.is_pinned = any(group_equal(g, self.sentence_group) for g in pinned_groups)
        for line_widget in self.findChildren(TextLineWidget):
            line_widget.is_pinned = self.is_pinned
            if "pin" in line_widget.buttons:
                line_widget.buttons["pin"].setProperty("pinned", "true" if self.is_pinned else "false")
                line_widget.buttons["pin"].style().unpolish(line_widget.buttons["pin"])
                line_widget.buttons["pin"].style().polish(line_widget.buttons["pin"])
        reset_global_timer()

    def enterEvent(self, event):
        global mouse_hover_count, global_timer
        if not self.underMouse():
            return
        mouse_hover_count += 1
        if global_timer and global_timer.isActive():
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
    """复用窗口的核心逻辑：匹配数据→复用窗口→更新布局（新增开关逻辑）"""
    global is_widgets_visible

    # ========== 核心修改：开关逻辑 ==========
    # 如果当前窗口是显示状态 → 直接隐藏并返回
    if is_widgets_visible:
        hide_all_widgets()
        return

    # 隐藏状态 → 执行「显示+更新」逻辑
    # ======================================

    # 收集需要显示的所有组
    display_groups = []
    for i, group in enumerate(pinned_groups):
        display_groups.append(("pinned", i, group))
    for i, group in enumerate(unpinned_groups):
        display_groups.append(("unpinned", i, group))

    if not display_groups:
        is_widgets_visible = False
        return

    global cached_widgets, active_displayed_widgets, mouse_hover_count
    mouse_hover_count = 0
    if global_timer and global_timer.isActive():
        global_timer.stop()

    # 第一步：匹配缓存窗口和需要显示的组
    used_cache_indices = []
    for display_idx, (group_type, idx, group) in enumerate(display_groups):
        # 查找匹配的缓存窗口
        matched_widget = None
        for cache_idx, w in enumerate(cached_widgets):
            if cache_idx in used_cache_indices:
                continue
            if group_equal(w.sentence_group, group):
                matched_widget = w
                used_cache_indices.append(cache_idx)
                break

        # 无匹配则创建新窗口
        if not matched_widget:
            matched_widget = RoundedWidget(group, group=group_type, index=idx)
            # 设置窗口属性
            flags = Qt.WindowFlags()
            if panel_config["global"]["window_frameless"]:
                flags |= Qt.FramelessWindowHint
            if panel_config["global"]["window_stay_on_top"]:
                flags |= Qt.WindowStaysOnTopHint
            flags |= Qt.Tool | Qt.WindowDoesNotAcceptFocus
            matched_widget.setWindowFlags(flags)
            matched_widget.setAttribute(Qt.WA_TranslucentBackground)
            cached_widgets.append(matched_widget)

        # 更新窗口数据（即使匹配也要更新索引/类型）
        matched_widget.update_group_data(group, group_type, idx)
        active_displayed_widgets.append(matched_widget)

    # 第二步：根据配置的排列方式布局
    match panel_config["global"]["history_panel_arrange_method"]:
        case 0:
            arrange_method_0(active_displayed_widgets)
        case 1:
            arrange_method_1(active_displayed_widgets)

    # 第三步：显示所有需要展示的窗口
    for w in active_displayed_widgets:
        w.show()

    # 更新显示状态标记
    is_widgets_visible = True


def arrange_method_1(display_widgets):
    """按列排列 - 复用窗口版本"""
    base_x = panel_config["widget"]["initial_x"]
    base_y = panel_config["widget"]["initial_y"]
    spacing = panel_config["widget"]["spacing"]
    widget_width = panel_config["widget"]["width"]

    primary_screen = QGuiApplication.primaryScreen()
    screen_geo = primary_screen.availableGeometry()
    screen_bottom = screen_geo.bottom()
    screen_right = screen_geo.right()

    current_col_x = base_x
    current_col_y = base_y

    for w in display_widgets:
        w.adjustSize()

        # 检查是否需要换列
        widget_bottom = current_col_y + w.height()
        if widget_bottom > screen_bottom - 100:
            current_col_x += widget_width + spacing
            if current_col_x + widget_width > screen_right:
                current_col_x = base_x
                current_col_y = screen_bottom + spacing
            current_col_y = base_y

        # 定位窗口
        w.move(current_col_x, current_col_y)
        current_col_y += w.height() + spacing

    # 兜底处理
    if current_col_x + widget_width > screen_right and current_col_y > screen_bottom:
        current_y_reset = base_y
        for w in display_widgets:
            w.move(base_x, current_y_reset)
            current_y_reset += w.height() + spacing
            if current_y_reset > screen_bottom:
                break


def arrange_method_0(display_widgets):
    """单行排列 - 复用窗口版本"""
    base_x = panel_config["widget"]["initial_x"]
    base_y = panel_config["widget"]["initial_y"]
    current_y = base_y
    spacing = panel_config["widget"]["spacing"]

    for w in display_widgets:
        w.adjustSize()
        w.move(base_x, current_y)
        current_y += w.height() + spacing


# 模拟新增组
counter = 1


def simulate_new_group():
    global counter
    new_group = {
        'simplified': f"简体示例：你们好吗？山上的小朋友{counter}",
        'traditional': f"繁體示例：你們好嗎？山上的小朋友{counter}",
        'english': f"Example {counter}：How are you? The kids on the hill."
    }
    add_sentence_group(new_group)
    print(f"新增组 {counter}")
    counter += 1


# 键盘监听线程（按/键显示/隐藏窗口）
class KeyboardThread(QThread):
    trigger = Signal()

    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()

        keyboard.hook_key("]", handler, suppress=True)
        keyboard.wait()


if __name__ == "__main__":
    load_reviewed_lines()
    load_pinned()

    # 测试数据
    test_groups = [
        {
            'simplified': "你们好吗？山上的小朋友你们好吗？山上的小朋友你们好吗？山上的小朋友",
            'traditional': "你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友",
            'english': "How are you? The kids on the hill. How are you? The kids on the hill."
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

    # 定时新增测试组（3秒一次）
    timer = QTimer()
    timer.timeout.connect(simulate_new_group)
    timer.start(3000)

    sys.exit(app.exec())