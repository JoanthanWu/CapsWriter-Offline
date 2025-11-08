import sys
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt

class RoundedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # 設定文字樣式
        self.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 50px;
                padding: -2px;   /* 內距確保文字不會貼邊 */
            }
        """)
        self.adjustSize()  # 讓 QLabel 根據文字大小自動調整

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 畫一個剛好等於 label 大小的圓角矩形
        brush = QBrush(QColor(0, 0, 255, 200))  # 半透明藍色
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

        # 再畫文字
        super().paintEvent(event)

def main():
    app = QApplication(sys.argv)

    label = RoundedLabel("這是一串浮動文字")
    label.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool
    )
    label.setAttribute(Qt.WA_TranslucentBackground)

    # 放在螢幕左上角
    label.move(500, 500)

    # 點擊後關閉
    label.mousePressEvent = lambda event: label.close()

    label.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
