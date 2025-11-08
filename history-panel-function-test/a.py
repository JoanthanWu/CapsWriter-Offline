from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QFont
import sys

def show_widgets():
    # 建立主視窗
    w = QWidget()
    w.setWindowTitle("Demo: 背景 + 邊框 + 文字")
    w.resize(300, 150)

    # 設定背景顏色與邊框 (用 QSS)
    w.setStyleSheet("""
        QWidget {
            background-color: #f0f0f0;        /* 淺灰背景 */
            border: 2px solid #007acc;        /* 藍色邊框 */
            border-radius: 8px;               /* 圓角 */
        }
    """)

    # 加入文字
    label = QLabel("Hello PySide6")
    label.setFont(QFont("Arial", 16))
    label.setStyleSheet("color: #333333;")   # 深灰文字

    # 版面配置
    layout = QVBoxLayout(w)
    layout.addWidget(label)
    layout.setContentsMargins(20, 20, 20, 20)

    w.show()
    return w

if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = show_widgets()
    sys.exit(app.exec())
