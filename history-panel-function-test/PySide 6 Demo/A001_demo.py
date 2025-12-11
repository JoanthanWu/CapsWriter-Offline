# a.py
from PySide6.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
import sys

class Mygui(QWidget):
    def __init__(self):
        # 建立主窗口
        super().__init__()
        self.setWindowTitle("PySide6 按鈕 Demo")
        self.resize(500, 500)  # 設定大小 500x500
        # 設定背景顏色為藍色
        self.setStyleSheet("background-color: blue;")
        # 建立按鈕，文字是 ✍️
        self.button = QPushButton("✍️")
        self.button.setFixedSize(200, 100)  # 固定大小，讓符號顯示更居中
        self.button.setStyleSheet("""
            QPushButton {
                font-size: 10px;       /* 字體大小 */
                border-radius: 50px;   /* 圓角 */
                background-color: #F30333;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        # 佈局
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
