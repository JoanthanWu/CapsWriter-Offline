import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                               QHBoxLayout, QVBoxLayout, QFrame)
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout, QFont
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
import tomllib

import panelVal
with open("history_r.log", "a", encoding="utf-8") as f:
    f.write(f"in smart_history_actions_panel: id(panelVal.unpinned_groups) = {id(panelVal.unpinned_groups)})\n")
unpinned_groups = panelVal.unpinned_groups
# 配置文件路径
CONFIG_FILE = "history_panel_config.toml"

DEFAULT_CONFIG = {
    # 文本行定义（可自定义顺序、标题、键）
    "text_lines": [
        {"key": "simplified", "title": "简"},   # 简体
        {"key": "traditional", "title": "繁"}, # 繁体
        {"key": "english", "title": "译"}      # 英文
    ],
    # 标题文本配置
    "title": {
        "font_family": "Microsoft YaHei",
        "font_size": 9,
        "font_bold": True,
        "font_italic": False,
        "color": [252, 220, 129, 255],
        "bg_color": [0, 0, 0, 0],
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
        "show_review": True
    },
    # 全局行为配置
    "global": {
        "max_text_groups": 12,
        "auto_close_timeout": 1000,
        "window_stay_on_top": True,
        "window_frameless": True
    }
}



# 颜色转换辅助函数（列表转QColor和CSS格式）
def to_qcolor(color_list):
    """将[r, g, b, a]列表转换为QColor"""
    return QColor(*color_list)


def to_css_rgba(color_list):
    """直接使用 0-255 的 alpha 值（符合 Qt 兼容的格式）"""
    try:
        # 补全并校验颜色值（确保 r/g/b/a 在 0-255 范围内）
        if not isinstance(color_list, list):
            color_list = [255, 255, 204, 255]  # 默认标题色

        r = max(0, min(255, int(color_list[0]))) if len(color_list) > 0 else 255
        g = max(0, min(255, int(color_list[1]))) if len(color_list) > 1 else 255
        b = max(0, min(255, int(color_list[2]))) if len(color_list) > 2 else 204
        a = max(0, min(255, int(color_list[3]))) if len(color_list) > 3 else 255  # 保留 0-255

        return f"rgba({r}, {g}, {b}, {a})"  # 直接使用 a 的原始值（不除以 255）
    except Exception as e:
        print(f"颜色解析错误：{e}，使用默认色")
        return "rgba(255, 255, 204, 255)"  # 默认标题色（alpha=255）


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
# unpinned_groups = []
active_widgets = []
global_timer = None
mouse_hover_count = 0


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


# 核心逻辑
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

# --------------------------------------------------------测试数据
    # 測試輸出：寫入文件
    with open("history_received_text.log", "a", encoding="utf-8") as f:
        f.write(f"[add_sentence_group 接收到] {new_group}\n")
# 测试数据 ---------------------------------------------------

    for key in ['simplified', 'traditional', 'english']:
        text = new_group.get(key, '').strip()
        if text and text in reviewed_lines:
            print(f"审查拦截：'{text}'")

# --------------------------------------------------------测试数据
            with open("history_received_text.log", "a", encoding="utf-8") as f:
                f.write(f"[add_sentence_group拦截之后 接收到] {new_group}\n")
# 测试数据 ---------------------------------------------------

            return

    for pg in pinned_groups:
        if group_equal(pg, new_group):
            return
    for ug in unpinned_groups:
        if group_equal(ug, new_group):
            return

    unpinned_groups.append(new_group)
    max_unpinned = MAX_TEXT_GROUPS - len(pinned_groups)
    while len(unpinned_groups) > max_unpinned:
        unpinned_groups.pop(0)
        print("移除最旧未钉住组")


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
        # self.fixed_width = panel_config["content"]["width"]
        self.ellipsis = panel_config["content"]["ellipsis"]
        self.setWordWrap(True)
        # self.setFixedWidth(self.fixed_width)
        # 内容标签背景色（透明）
        self.setStyleSheet(f"background-color: {to_css_rgba(panel_config['content']['bg_color'])};")
        # 解除宽度限制
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        # 新增：设置内容字体（包含粗体和斜体）
        font = QFont(
            panel_config["content"]["font_family"],
            panel_config["content"]["font_size"]
        )
        font.setBold(panel_config["content"]["font_bold"])  # 应用粗体配置
        font.setItalic(panel_config["content"]["font_italic"])  # 应用斜体配置
        self.setFont(font)

    def setText(self, text):
        fm = QFontMetrics(self.font())
        line_height = fm.lineSpacing() + panel_config["content"]["line_spacing"]

        # 关键：获取父容器（TextLineWidget）的总宽度（即widget分配给该行的宽度）
        if self.parent() and self.parent().width() > 0:
            # 总宽度 = 父容器宽度 - 标题宽度 - 两边边距（避免溢出）
            parent_width = self.parent().width()
            title_width = self.parent().title_label.width()  # 标题实际宽度
            layout_width = parent_width - title_width - 20  # 减20避免边距挤压
        else:
            #  fallback：使用配置的content.width（500）
            layout_width = panel_config["content"].get("width", 500)

        # 确保最小宽度（避免过窄）
        layout_width = max(layout_width, 100)

        # 以下是原有的文本换行逻辑（使用计算出的layout_width）
        layout = QTextLayout(text, self.font())
        layout.beginLayout()
        lines = []
        more_lines_exist = False
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(layout_width)  # 使用计算出的可用宽度
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
            # 用计算出的layout_width判断是否需要省略号
            while last_line and fm.horizontalAdvance(last_line + self.ellipsis) > layout_width:
                last_line = last_line[:-1]
            lines[-1] = last_line + self.ellipsis

        actual_lines = len(lines)
        self.setFixedHeight(actual_lines * line_height)  # 高度自适应行数
        super().setText("\n".join(lines))


class TextLineWidget(QWidget):
    def __init__(self, text, title, is_pinned, is_reviewing, parent=None):
        super().__init__(parent)
        self.text = text
        self.parent_widget = parent
        self.is_pinned = is_pinned
        self.is_reviewing = is_reviewing

        # 容器背景透明（继承父容器颜色）
        self.setStyleSheet("")

        self.line_layout = QHBoxLayout(self)
        self.line_layout.setSpacing(panel_config["content"]["line_spacing"])
        # 读取配置的内边距（左、上、右、下）
        margins = panel_config["content"]["margins"]
        # 容错处理：确保参数是4个整数
        if not isinstance(margins, list) or len(margins) != 4:
            margins = [0, 0, 0, 0]  # 默认为0
        left, top, right, bottom = margins
        self.line_layout.setContentsMargins(left, top, right, bottom)  # 应用自定义内边距

        # 标题标签（自适应宽度）
        self.title_label = QLabel(title)
        # 新增：设置标题字体（包含粗体和斜体）
        font = QFont(
            panel_config["title"]["font_family"],
            panel_config["title"]["font_size"]
        )
        font.setBold(panel_config["title"]["font_bold"])  # 应用粗体配置
        font.setItalic(panel_config["title"]["font_italic"])  # 应用斜体配置
        self.title_label.setFont(font)

        style_sheet = f"""
            color: {to_css_rgba(panel_config["title"]["color"])};
            background-color: {to_css_rgba(panel_config["title"]["bg_color"])};
            border: {panel_config["title"]["border_width"]}px solid {to_css_rgba(panel_config["title"]["border_color"])};
            padding: 0 {panel_config["title"]["padding"]}px;
        """
        self.title_label.setStyleSheet(style_sheet)

        # 计算标题文字的实际宽度（根据字体和内容）
        font_metrics = self.title_label.fontMetrics()
        text_width = font_metrics.horizontalAdvance(title)  # 文字本身宽度
        total_width = text_width + 2 * panel_config["title"]["padding"]  # 加上左右内边距

        # 应用 min/max 宽度限制（来自配置）
        min_width = panel_config["title"]["min_width"]
        max_width = panel_config["title"]["max_width"]
        final_width = max(min_width, min(total_width, max_width))  # 限制在 [min, max] 范围内
        self.title_label.setFixedWidth(final_width)  # 标题固定为计算后的宽度

        self.line_layout.addWidget(self.title_label)

        # 内容标签（占据剩余空间）
        self.content_label = MultiLineElidedLabel(text)
        self.content_label.setFont(QFont(
            panel_config["content"]["font_family"],
            panel_config["content"]["font_size"]
        ))
        self.content_label.setStyleSheet(f"""
            color: {to_css_rgba(panel_config["content"]["color"])};
            background-color: {to_css_rgba(panel_config["content"]["bg_color"])};
            border: {panel_config["content"]["border_width"]}px solid {to_css_rgba(panel_config["content"]["border_color"])};
        """)
        self.content_label.setText(text)

        # 布局拉伸设置（核心）
        # 标题拉伸因子为 0（不拉伸，保持自身宽度）
        # 内容拉伸因子为 1（占据所有剩余空间）
        self.line_layout.addWidget(self.title_label, stretch=0)
        self.line_layout.addWidget(self.content_label, stretch=1)

        # 按钮容器（背景透明）
        self.buttons_container = QWidget(self)
        self.buttons_container.setAttribute(Qt.WA_TranslucentBackground)
        # self.buttons_container.setStyleSheet("")
        self.buttons_container.hide()


        # 按钮布局
        btn_layout = QHBoxLayout(self.buttons_container)
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # 按钮顺序：pin → copy → paste → type → 横线 → review
        button_order = ["pin", "copy", "paste", "type", "review"]
        self.buttons = {}
        for name in button_order:
            if panel_config["button"][f"show_{name}"]:
                if name == "pin":
                    self.buttons[name] = QPushButton("📌")
                elif name == "copy":
                    self.buttons[name] = QPushButton("📑")
                elif name == "paste":
                    self.buttons[name] = QPushButton("📋")
                elif name == "type":
                    self.buttons[name] = QPushButton("✍️")
                elif name == "review":
                    self.buttons[name] = QPushButton("⛓")

        # 设置按钮属性
        for name, btn in self.buttons.items():
            btn.setObjectName(f"btn_{name}")
            if name == "pin":
                btn.setProperty("pinned", "true" if self.is_pinned else "false")
            if name == "review":
                btn.setProperty("reviewing", "true" if self.is_reviewing else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # 绑定事件
        if "pin" in self.buttons:
            self.buttons["pin"].clicked.connect(self.pin_group)
        if "copy" in self.buttons:
            self.buttons["copy"].clicked.connect(self.copy_only)
        if "paste" in self.buttons:
            self.buttons["paste"].clicked.connect(self.copy_and_paste)
        if "type" in self.buttons:
            self.buttons["type"].clicked.connect(self.simulate_typing)
        if "review" in self.buttons:
            self.buttons["review"].clicked.connect(self.toggle_review)

        # 添加按钮到布局（前4个→横线→第5个）
        btn_w, btn_h = panel_config["button"]["size"]
        button_list = list(self.buttons.items())

        # 前4个按钮
        for i, (name, btn) in enumerate(button_list[:4]):
            btn.setFixedSize(btn_w, btn_h)
            btn_layout.addWidget(btn)

        # 横线（仅当有第5个按钮）
        if len(button_list) >= 5:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setFixedWidth(18)
            sep_color = to_css_rgba(panel_config['unpinned']['border_colors'][0])
            separator.setStyleSheet(f"border: 3px solid {sep_color}; background-color: transparent;")
            btn_layout.addWidget(separator, alignment=Qt.AlignCenter)

            # 第5个按钮（review）
            name, btn = button_list[4]
            btn.setFixedSize(btn_w, btn_h)
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

    # 按钮功能
    def copy_only(self):
        QApplication.clipboard().setText(self.text)
        print(f"已复制: {self.text[:20]}...")
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
        if "pin" in self.buttons:
            self.buttons["pin"].setProperty("pinned", "true" if self.is_pinned else "false")
            self.buttons["pin"].style().unpolish(self.buttons["pin"])
            self.buttons["pin"].style().polish(self.buttons["pin"])
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

        # 创建文本行
        for line_config in panel_config["text_lines"]:
            key = line_config["key"]  # 如 "simplified"
            title = line_config["title"]  # 如 "简："
            self.create_text_line(key, title)  # 调用原方法创建

        # 应用按钮样式
        self.setStyleSheet(self._get_stylesheet())
        self.setFixedWidth(panel_config["widget"]["width"])
        self.adjustSize()

    def _get_stylesheet(self):
        """使用自定义 hover 颜色：区分 pinned/reviewing 的 true/false 状态"""
        # 转换颜色为 CSS 格式
        normal_color = to_css_rgba(panel_config['button']['normal_color'])
        hover_color = to_css_rgba(panel_config['button']['hover_color'])  # false 状态 hover
        pinned_color = to_css_rgba(panel_config['button']['pinned_color'])
        pinned_hover_color = to_css_rgba(panel_config['button']['pinned_hover_color'])  # true 状态 hover
        review_color = to_css_rgba(panel_config['button']['review_color'])
        review_hover_color = to_css_rgba(panel_config['button']['review_hover_color'])  # true 状态 hover
        border_color = to_css_rgba(panel_config['unpinned']['border_colors'][0])

        return f"""
            /* 基础样式 */
            QPushButton {{
                border: 1px solid {border_color};
                background-color: {normal_color};
                padding: 0px;
                margin: 0px;
                font-size: 12px;
            }}

            /* 按钮形状 */
            QPushButton#btn_pin {{
                border-top-left-radius: {panel_config['button']['border_radius']}px;
                border-bottom-left-radius: {panel_config['button']['border_radius']}px;
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

            /* Pin 按钮状态 */
            QPushButton#btn_pin[pinned="true"] {{
                background-color: {pinned_color};  /* true 正常状态 */
            }}
            QPushButton#btn_pin[pinned="false"] {{
                background-color: {normal_color};  /* false 正常状态 */
            }}

            /* Review 按钮状态 */
            QPushButton#btn_review[reviewing="true"] {{
                background-color: {review_color};  /* true 正常状态 */
            }}
            QPushButton#btn_review[reviewing="false"] {{
                background-color: {normal_color};  /* false 正常状态 */
            }}

            /* Hover 状态（核心：区分 true/false） */
            QPushButton#btn_pin[pinned="true"]:hover {{
                background-color: {pinned_hover_color};  /* pinned=true 时用专用 hover 色 */
            }}
            QPushButton#btn_pin[pinned="false"]:hover {{
                background-color: {hover_color};  /* pinned=false 时用通用 hover 色 */
            }}

            QPushButton#btn_review[reviewing="true"]:hover {{
                background-color: {review_hover_color};  /* reviewing=true 时用专用 hover 色 */
            }}
            QPushButton#btn_review[reviewing="false"]:hover {{
                background-color: {hover_color};  /* reviewing=false 时用通用 hover 色 */
            }}

            /* 其他按钮（copy/paste/type）使用通用 hover 色 */
            QPushButton#btn_copy:hover,
            QPushButton#btn_paste:hover,
            QPushButton#btn_type:hover {{
                background-color: {hover_color};
            }}
        """
    def _calc_background_size(self):
        content_height = self.main_layout.sizeHint().height()
        pad_top, _, pad_bottom, _ = panel_config["widget"]["padding"]
        bg_height = content_height + pad_top + pad_bottom
        bg_width = panel_config["widget"]["width"]  # 强制使用配置的宽度（700）
        return bg_width, bg_height
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
        bg_width = panel_config["widget"]["width"]  # 强制使用配置的宽度（700）
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

        # 背景和边框颜色（直接用QColor解析列表）
        if self.group == "pinned":
            colors = panel_config["pinned"]["bg_colors"]
            border_colors = panel_config["pinned"]["border_colors"]
        else:
            colors = panel_config["unpinned"]["bg_colors"]
            border_colors = panel_config["unpinned"]["border_colors"]

        color_idx = self.index % len(colors)
        bg_color = to_qcolor(colors[color_idx])  # 直接转换列表为QColor
        border_color = to_qcolor(border_colors[color_idx % len(border_colors)])

        # 绘制背景
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)

        # 绘制边框
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
    from panelVal import unpinned_groups as unpinned_groups
    with open("history_r.log", "a", encoding="utf-8") as f:
        f.write(f"in show_widgets: id(unpinned_groups) = {id(unpinned_groups)})\n")

    global active_widgets, mouse_hover_count
    base_x = panel_config["widget"]["initial_x"]
    base_y = panel_config["widget"]["initial_y"]
    current_y = base_y
    spacing = panel_config["widget"]["spacing"]

    if active_widgets:
        close_all_widgets()
        return

    mouse_hover_count = 0
    if global_timer and global_timer.isActive():
        global_timer.stop()

    # 显示固定组
    for i, group in enumerate(pinned_groups):
        w = RoundedWidget(group, group="pinned", index=i)
        flags = Qt.WindowFlags()
        if panel_config["global"]["window_frameless"]:
            flags |= Qt.FramelessWindowHint
        if panel_config["global"]["window_stay_on_top"]:
            flags |= Qt.WindowStaysOnTopHint
        flags |= Qt.Tool | Qt.WindowDoesNotAcceptFocus
        w.setWindowFlags(flags)
        w.setAttribute(Qt.WA_TranslucentBackground)  # 允许背景透明
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing

    # 显示非固定组
    for i, group in enumerate(unpinned_groups):
        w = RoundedWidget(group, group="unpinned", index=i)
        flags = Qt.WindowFlags()
        if panel_config["global"]["window_frameless"]:
            flags |= Qt.FramelessWindowHint
        if panel_config["global"]["window_stay_on_top"]:
            flags |= Qt.WindowStaysOnTopHint
        flags |= Qt.Tool | Qt.WindowDoesNotAcceptFocus
        w.setWindowFlags(flags)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        current_y += w.height() + spacing


# 模拟新增组
counter = 1
# 新增prefix参数，用于接收前缀文字
def simulate_new_group(prefix):
    global counter
    new_group = {
        # 拼接前缀：f"{prefix} " + 原有内容（注意加空格分隔）
        'simplified': f"{prefix} 简体示例：你们好吗？山上的小朋友",
        'traditional': f"{prefix} 繁體示例：你們好嗎？山上的小朋友",
        'english': f"{prefix} Example {counter}：How are you? The kids on the hill."
    }
    add_sentence_group(new_group)
    print(f"新增组 {counter}")
    counter += 1
    if active_widgets:
        close_all_widgets()
        show_widgets()
    # if active_widgets and self.widget is not None:  # 确保窗口已创建
        # # 1. 隐藏窗口
        # self.widget.hide()
        # # 2. 刷新窗口数据（调用面板的refresh_data方法）
        # self.widget.refresh_data()
        # # 3. 重新显示窗口（此时显示的是最新数据）
        # self.widget.show()


# 键盘监听线程（按z键显示/隐藏窗口）
class KeyboardThread(QThread):
    trigger = Signal()

    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()
                with open("history_r.log", "a", encoding="utf-8") as f:
                    f.write(
                        f"in KeyboardThread : id(unpinned_groups) = {id(unpinned_groups)})\n")
        keyboard.hook_key("/", handler, suppress=True)
        keyboard.wait()


if __name__ == "__main__":
    load_reviewed_lines()
    load_pinned()

    # 测试数据z
    test_groups = [
        {
            'simplified': "你们好吗？山上的小朋友你们好吗？山上的小朋友你们好吗？山上的小朋友你们好吗？山上的小朋友你们好吗？山上的小朋友你们好吗？山上的小朋友你们好吗？山上的小朋友",
            'traditional': "你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 你們好嗎？山上的小朋友 ",
            'english': "How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. How are you? The kids on the hill. "
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

    timer = QTimer()
    timer.timeout.connect(simulate_new_group)
    timer.start(3000)

    sys.exit(app.exec())

