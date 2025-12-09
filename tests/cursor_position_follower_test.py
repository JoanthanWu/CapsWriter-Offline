import sys

import win32api
import win32con
import win32gui
import win32print
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QLabel


class Cursor_Position(QLabel):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.resize(150, 20)
        font = QFont("Segoe MDL2 Assets", 14)
        self.setFont(font)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#212121"))  # 设置背景颜色
        palette.setColor(QPalette.WindowText, QColor("#00B294"))  # 设置文本颜色
        self.setPalette(palette)

        # 创建一个定时器来定期更新鼠标位置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tooltip_position)
        self.timer.start(100)  # 每100毫秒更新一次

    def update_tooltip_position(self):
        # 使用pywin32获取全局鼠标位置
        x, y = win32api.GetCursorPos()
        global scale_x, scale_y
        print(f"屏幕缩放比例: {scale_x}, {scale_y}")
        x, y = x / scale_x, y / scale_y
        print(x, y)
        # 更新标签的位置和文本
        self.move(x + (20 / scale_x), y + (20 / scale_y))
        self.setText(f"X: {int(x)}, Y: {int(y)}")
        self.setVisible(True)


def Print_Screen_Scale():
    # 获取屏幕的宽度和高度
    hDC = win32gui.GetDC(0)
    screen_width = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    screen_height = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    print(f"屏幕尺寸: {screen_width}x{screen_height}")
    # 获取逻辑的宽度和高度
    logical_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    logical_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    print(f"逻辑尺寸: {logical_width}x{logical_height}")
    # 计算缩放比例
    global scale_x, scale_y
    scale_x = screen_width / logical_width
    scale_y = screen_height / logical_height
    print(f"屏幕缩放比例: {scale_x}, {scale_y}")


if __name__ == "__main__":
    Print_Screen_Scale()

    app = QApplication(sys.argv)
    window = Cursor_Position()
    window.setWindowTitle("Cursor Position Follower")
    window.show()
    sys.exit(app.exec())
