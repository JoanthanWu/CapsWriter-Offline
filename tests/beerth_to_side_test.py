import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.edgeMargin = 10
        self.isBerthLeft = False
        self.isBerthRight = False

    def initUI(self):
        self.resize(425, 425)
        self.setWindowTitle("Window Title")
        self.setWindowOpacity(0.9)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)
        self.label = QLabel("窗口左右停靠演示", self)
        self.label.setGeometry(10, 10, 425, 425)

        # 创建一个定时器，每隔三秒检查窗口状态
        self.timer = QTimer(self)
        # self.timer.timeout.connect(self.checkWindowActive)
        self.timer.start(3000)  # 3000毫秒间隔

    def checkWindowActive(self):
        # 检查窗口是否处于活跃状态
        if self.isActiveWindow():
            self.label.setText("窗口活跃状态")
            pass
        else:
            self.label.setText("窗口不活跃状态")
            x, y, width, height, screenWidth, screenHeight = self.checkWindowInfo()
            if x == 0:  # 窗口非活跃状态，从左边弹出的，恢复继续停靠在左边
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif (
                x == screenWidth - width
            ):  # 窗口非活跃状态，从右边弹出的，恢复继续停靠在右边
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            else:
                print("窗口无需恢复停靠")
                pass

    def enterEvent(self, event):
        super().enterEvent(event)
        print("enterEvent")
        x, y, width, height, screenWidth, screenHeight = self.checkWindowInfo()
        if self.isBerthLeft:  # 已停靠在左边
            self.move(0, y - 31)  # 从左边弹出，31是标题栏高度
            self.isBerthLeft = False
        elif self.isBerthRight:  # 已停靠在右边
            self.move(screenWidth - width, y - 31)  # 从右边弹出，31是标题栏高度
            self.isBerthRight = False
        else:
            print("窗口未停靠")

    def leaveEvent(self, event):
        super().leaveEvent(event)
        print("leaveEvent")
        x, y, width, height, screenWidth, screenHeight = self.checkWindowInfo()
        print(
            f"左右，高低，宽，高，屏宽，屏高: {(x, y, width, height, screenWidth, screenHeight)}"
        )
        if self.isActiveWindow():  # 窗口活跃状态，用户点击了窗口，则不恢复继续停靠
            self.label.setText("窗口活跃状态")
            print("窗口活跃状态")
            if x < 0 - width / 2:
                print("活跃状态，但是窗口的一半已超出屏幕左边界，将窗口停靠在左边")
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif x > screenWidth - width / 2:
                print("窗口活跃状态，但是窗口的一半已超出屏幕右边界，将窗口停靠在右边")
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            else:
                print("窗口活跃状态，无需停靠")
                pass
        else:  # 窗口非活跃状态，用户可能只是鼠标划过看一眼，失去焦点时恢复继续停靠
            self.label.setText("窗口不活跃状态")
            print("窗口不活跃状态")
            if x < 0 - width / 2:
                print("窗口的一半已超出屏幕左边界")
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif x > screenWidth - width / 2:
                print("窗口的一半已超出屏幕右边界")
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            elif x == 0:  # 窗口非活跃状态，从左边弹出的，恢复继续停靠在左边
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif (
                x == screenWidth - width
            ):  # 窗口非活跃状态，从右边弹出的，恢复继续停靠在右边
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            else:
                print("窗口未超出屏幕边界")
                pass

    def berthToLeft(self, x, y, width, height, screenWidth, screenHeight):
        self.move(0 - width + self.edgeMargin, y - 31)  # 停靠到左边，31是标题栏高度
        self.isBerthLeft = True

    def berthToRight(self, x, y, width, height, screenWidth, screenHeight):
        self.move(screenWidth - self.edgeMargin, y - 31)  # 停靠到右边，31是标题栏高度
        self.isBerthRight = True

    def checkWindowInfo(self):
        geometry = self.geometry()
        x = geometry.x()
        y = geometry.y()
        width = geometry.width()
        height = geometry.height()
        primaryScreen = QApplication.instance().primaryScreen()
        screenRect = primaryScreen.geometry()
        screenWidth = screenRect.width()
        screenHeight = screenRect.height()
        return x, y, width, height, screenWidth, screenHeight


def test_gui():
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_gui()
