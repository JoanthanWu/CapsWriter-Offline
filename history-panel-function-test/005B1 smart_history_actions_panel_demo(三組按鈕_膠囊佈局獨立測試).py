import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout

class CapsuleButtons(QWidget):
    def __init__(self):
        super().__init__()

        # 三顆按鈕
        # btn1 = QPushButton("Copy")
        # btn2 = QPushButton("Paste")
        # btn3 = QPushButton("Type")
        btn1 = QPushButton("📑")      # Copy
        btn2 = QPushButton("📋")     # Copy+Paste
        btn3 = QPushButton("✍️")      # 模擬打字

        # 設定 objectName 方便 QSS 定位
        btn1.setObjectName("btn_left")
        btn2.setObjectName("btn_mid")
        btn3.setObjectName("btn_right")

        # 固定大小讓它們看起來一致
        for b in (btn1, btn2, btn3):
            b.setFixedHeight(32)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(btn3)
        self.setLayout(layout)

        # 套用樣式表
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid rgba(255,244,115,200);
                background-color: rgba(255,209,64,180);
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,150);
            }

            QPushButton#btn_left {
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
                border-right: none;
            }
            QPushButton#btn_mid {
                border-radius: 0;
                border-right: none;
            }
            QPushButton#btn_right {
                border-top-right-radius: 16px;
                border-bottom-right-radius: 16px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CapsuleButtons()
    w.show()
    sys.exit(app.exec())
