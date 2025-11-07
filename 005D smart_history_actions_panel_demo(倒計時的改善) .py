import sys
import time
import keyboard
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QTimer, QThread, Signal

current_widget = None
pinned_state = False   # 全域變數，記錄釘住狀態

class KeyboardThread(QThread):
    trigger = Signal()
    def run(self):
        def handler(e):
            if e.event_type == "down":  # 只在按下時觸發
                self.trigger.emit()
        keyboard.hook_key("z", handler, suppress=True)
        keyboard.wait()

class RoundedWidget(QWidget):
    def __init__(self, text="", parent=None, pinned=False):
        super().__init__(parent)
        self.pinned = pinned

        self.label = QLabel(text)
        self.label.setStyleSheet("color: white; font-size: 20px;")

        # 4個小按鈕
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
        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.btn_pin)
        button_layout.addWidget(self.btn_copy)
        button_layout.addWidget(self.btn_paste)
        button_layout.addWidget(self.btn_type)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_layout)
        self.adjustSize()

        # 設定 objectName
        self.btn_pin.setObjectName("btn_pin")
        self.btn_copy.setObjectName("btn_copy")
        self.btn_paste.setObjectName("btn_paste")
        self.btn_type.setObjectName("btn_type")

        # 設定屬性 pinned
        self.btn_pin.setProperty("pinned", str(self.pinned).lower())

        # 建立一個持久 QTimer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)

        # 如果不是釘住狀態，初始化時就啟動倒計時
        if not self.pinned:
            self.timer.start(10000)

        # 樣式表：根據 pinned 屬性切換顏色
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(255,244,115,200);
                background-color: rgba(255,209,64,180);
                padding: 0px;
                margin: 0px;
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
                background-color: rgba(255,100,100,180);
            }
            QPushButton#btn_pin[pinned="false"] {
                background-color: rgba(255,209,64,180);
            }
            
            /* hover 規則放在最後，確保其他按鈕也能生效 */
            QPushButton:hover {
                background-color: rgba(255,255,255,150);
            }
            QPushButton#btn_pin[pinned="true"]:hover {
                background-color: rgba(200,50,50,200);
            }
            QPushButton#btn_pin[pinned="false"]:hover {
                background-color: rgba(255,255,255,150);
            }
        """)

    def set_text(self, text):
        self.label.setText(text)
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor(0, 0, 255, 128))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        super().paintEvent(event)

    # 功能1：單純複製
    def copy_only(self):
        QApplication.clipboard().setText(self.label.text())
        print("已複製:", self.label.text())

    # 功能2：複製+貼上
    # 功能2：複製+貼上
    def copy_and_paste(self):
        QApplication.clipboard().setText(self.label.text())
        time.sleep(0.1)
        keyboard.send("ctrl + v")
        print("功能2：複製+貼上")
        if not self.pinned:
            self.close()

    # 功能3：模擬打字
    def simulate_typing(self):
        keyboard.write(self.label.text())
        print("功能3：模擬打字")
        if not self.pinned:
            self.close()

    # 功能4：釘住文字
    def pin_text(self):
        global pinned_state
        self.pinned = not self.pinned
        pinned_state = self.pinned
        self.btn_pin.setProperty("pinned", str(self.pinned).lower())
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)
        self.btn_pin.update()
        print("釘住狀態:", self.pinned)

        # 如果釘住 → 停止計時器；取消釘住 → 重新啟動
        if self.pinned:
            self.timer.stop()
        else:
            self.timer.start(10000)

def show_widget():
    global current_widget, pinned_state
    if current_widget is None or not current_widget.isVisible():
        current_widget = RoundedWidget("這是一串浮動文字", pinned=pinned_state)
        current_widget.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        current_widget.setAttribute(Qt.WA_TranslucentBackground)
        current_widget.move(100, 100)
        current_widget.show()
    else:
        current_widget.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(show_widget)
    kb_thread.start()
    sys.exit(app.exec())
