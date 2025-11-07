import sys
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import Qt

def main():
    app = QApplication(sys.argv)

    label = QLabel("這是一串浮動文字")
    label.setStyleSheet("""
        QLabel {
            color: red;
            font-size: 32px;
            background-color: rgba(0, 0, 0, 0);
        }
    """)

    label.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool
    )
    label.setAttribute(Qt.WA_TranslucentBackground)
    label.adjustSize()

    # 指定位置：螢幕左上角
    label.move(0, 0)

    # 點擊後關閉
    label.mousePressEvent = lambda event: label.close()

    label.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
