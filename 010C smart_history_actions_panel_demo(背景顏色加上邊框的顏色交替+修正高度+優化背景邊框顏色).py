import sys
import time
import json
import os
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush, QFontMetrics, QPen, QTextLayout
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize

MAX_TOTAL = 12
pinned_sentences = []
unpinned_sentences = []
active_widgets = []
global_timer = None
PINNED_FILE = "pinned.json"

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
        # 初始化时调用setText，内部会处理高度计算
        # 下面這句是導致強制文字字體大小的元兇!!!!!!!!!!!
        # self.setText(text)  # 这里会触发setText方法，内部计算高度

    def setText(self, text):
        # 1. 计算字体相关参数（line_height是局部变量，仅在此方法内有效）
        fm = QFontMetrics(self.font())
        print("当前字体大小:", self.font().pointSize())  # 若打印值不是18，说明字体未更新
        line_height = fm.lineSpacing()  # 局部变量：仅在setText内部可用

        # 2. 处理文本换行和省略号
        layout = QTextLayout(text, self.font())
        layout.beginLayout()
        lines = []  # 初始化行列表
        more_lines_exist = False  # 初始化是否有更多行的标记
        while True:
            line = layout.createLine()
            if not line.isValid():
                break  # 没有更多行时退出循环
            line.setLineWidth(self.fixed_width)
            start = line.textStart()
            length = line.textLength()
            lines.append(text[start:start + length])
            # 如果达到最大行数，检查是否还有剩余内容
            if len(lines) >= self.max_lines:
                if layout.createLine().isValid():
                    more_lines_exist = True
                break
        layout.endLayout()

        # 3. 处理省略号（仅当有更多行且lines不为空时）
        if more_lines_exist and lines:
            last_line = lines[-1]
            # 确保加上省略号后不超过宽度
            while last_line and fm.horizontalAdvance(last_line + self.ellipsis) > self.fixed_width:
                last_line = last_line[:-1]
            lines[-1] = last_line + self.ellipsis

        # 4. 计算实际行数并设置高度（关键：line_height在这里使用，作用域正确）
        actual_lines = len(lines)
        self.setFixedHeight(actual_lines * line_height)  # 这里使用的是当前方法内的line_height

        # 5. 最终设置处理后的文本
        super().setText("\n".join(lines))


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
            fixed_width=300,
            ellipsis="[...]"
        )
        # !!!!! 通过样式表设置的font-size: 18px没有被QFontMetrics正确识别，导致MultiLineElidedLabel始终基于默认字体大小（9 点）计算高度。
        # self.label.setStyleSheet("color: white; font-size: 18px;")

        # 直接通过QFont设置字体大小（关键：不依赖样式表）
        font = self.label.font()  # 获取当前字体
        font.setPointSize(12)  # 设置为18点（对应约24px，确保清晰）
        self.label.setFont(font)  # 应用字体
        self.label.setStyleSheet("color: white;")  # 仅保留颜色样式
        self.label.setText(text)  # 强制重新计算高度

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

        # 主 layout（减少内边距，避免挤压绘制区域）
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(3, 3, 3, 3)  # 原先是(5,5,5,5)，适当减小

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

        # 初始化大小
        self.adjustSize()

    # 修正背景大小计算，基于label的实际高度
    def _calc_background_size(self):
        line_height = self.label.fontMetrics().lineSpacing()
        actual_lines = self.label.height() // line_height  # 1或2行

        padding_y = int(line_height * 0.3)  # 内边距保持不变
        # 确保背景高度计算准确（label高度 + 上下内边距）
        bg_height = self.label.height() + padding_y * 2
        bg_width = self.label.width() + 14  # 宽度保持不变
        return bg_width, bg_height

    def sizeHint(self):
        bg_width, bg_height = self._calc_background_size()
        # 直接返回计算的宽高作为理想大小
        return QSize(bg_width, bg_height)

    def setLabelFontSize(self, px: int):
        # 1. 修改字体大小样式
        self.label.setStyleSheet(f"color: white; font-size: {px}px;")
        # 2. 强制label重新计算文本布局和高度（关键步骤）
        current_text = self.label.text()  # 获取当前文本
        self.label.setText(current_text)  # 重新设置文本，触发高度计算
        # 3. 更新Widget自身的布局和大小
        self.updateGeometry()  # 通知布局管理器尺寸可能变化
        self.adjustSize()  # 强制重新计算大小
        self.update()  # 刷新绘制

    def total_height(self):
        # 返回包含边框的总高度（如果边框线宽2px，可能需要加2）
        return self.height()  # 如果之前的paintEvent已正确包含边框，直接返回height即可

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

    # 修正paintEvent，移除强制固定高度的逻辑
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_width, bg_height = self._calc_background_size()
        border_radius = 8

        # 关键：强制widget高度等于bg_height（确保绘制区域足够）
        if self.height() != bg_height:
            self.setFixedHeight(bg_height)
        if self.width() != bg_width:
            self.setFixedWidth(bg_width)

        # 选择颜色组
        if self.group == "pinned":
            bg_color, border_color = PINNED_COLORS[self.index % 2]
        else:
            bg_color, border_color = UNPINNED_COLORS[self.index % 2]

        # 画背景（填充）
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, bg_width, bg_height, border_radius, border_radius)

        # 画边框（注意线宽会占用1px，需微调避免被截断）
        pen = QPen(border_color)
        pen.setWidth(4)  # 线宽2px，需要确保不超出widget范围
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        # 调整矩形坐标：向右下偏移1px，避免边框的左/上边缘被线宽覆盖
        painter.drawRoundedRect(1, 1, bg_width - 2, bg_height - 2, border_radius, border_radius)

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
    current_y = base_y  # 用current_y追踪当前位置，避免直接修改y变量

    if active_widgets:
        close_all_widgets()
        return

    # 定义widget之间的间距（可根据需要调整，比如5px）
    spacing = 5

    # pinned
    for i, text in enumerate(pinned_sentences):
        w = RoundedWidget(text, group="pinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        # 强制刷新大小，确保获取准确的高度
        w.adjustSize()
        # 移动到当前y位置
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        # 更新current_y：当前y + widget实际高度 + 间距
        current_y += w.height() + spacing

    # unpinned
    for i, text in enumerate(unpinned_sentences):
        w = RoundedWidget(text, group="unpinned", index=i)
        w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.adjustSize()
        w.move(base_x, current_y)
        w.show()
        active_widgets.append(w)
        # 同样更新current_y，加上高度和间距
        current_y += w.height() + spacing


# -------------------模擬外部句子逐漸進來-------------------
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

# -------------------綁定按鍵-------------------
class KeyboardThread(QThread):
    trigger = Signal()
    def run(self):
        def handler(e):
            if e.event_type == "down":
                self.trigger.emit()
        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()

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
