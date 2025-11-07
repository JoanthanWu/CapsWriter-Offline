# a_2.py :
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QFont

def show_widgets():
    w = QWidget()
    w.setWindowTitle("Demo: 背景 + 邊框 + 文字")
    w.resize(300, 150)

    w.setStyleSheet("""
        QWidget {
            background-color: #f0f0f0;
            border: 2px solid #007acc;
            border-radius: 8px;
        }
    """)

    label = QLabel("Hello PySide6")
    label.setFont(QFont("Arial", 16))
    label.setStyleSheet("color: #333333;")

    layout = QVBoxLayout(w)
    layout.addWidget(label)
    layout.setContentsMargins(20, 20, 20, 20)

    w.show()
    return w
