import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
import a_2

class Controller:
    def __init__(self):
        # 只建立一次小窗口
        self.widget = a_2.create_widget()

    def toggle_widget(self):
        if self.widget.isVisible():
            self.widget.hide()
        else:
            self.widget.show()

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        # 綁定 / 鍵切換面板，全局有效
        shortcut = QShortcut(QKeySequence("/"), self)
        shortcut.setContext(Qt.ApplicationShortcut)
        shortcut.activated.connect(self.controller.toggle_widget)

        self.setWindowTitle("主視窗（按 / 切換小窗口）")
        self.resize(400, 300)
        self.show()

def run_app():
    app = QApplication(sys.argv)
    controller = Controller()
    window = MainWindow(controller)
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
