import sys

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QStyle,
    QSystemTrayIcon,
)
from qt_material import apply_stylesheet


class TrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        apply_stylesheet(
            self.app,
            theme="dark_teal.xml",
            css_file="util\\client\\gui_theme_custom.css",
        )
        self.tray_icon = QSystemTrayIcon()
        icon = self.app.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        # 创建托盘菜单
        self.tray_menu = QMenu()

        # 创建单选子菜单
        self.create_radio_menu()

        # 添加退出动作
        exit_action = QAction("退出", self.tray_menu)
        exit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def create_radio_menu(self):
        # 创建子菜单
        radio_menu = self.tray_menu.addMenu("选择模式")

        # 创建动作组实现单选功能
        action_group = QActionGroup(self.tray_menu)
        action_group.setExclusive(True)  # 让组内动作互斥（单选）

        # 添加单选项
        mode1 = QAction("模式1", radio_menu)
        mode1.setCheckable(True)
        mode1.setChecked(True)  # 默认选中第一个
        mode1.triggered.connect(lambda: self.mode_selected("模式1"))
        action_group.addAction(mode1)
        radio_menu.addAction(mode1)

        mode2 = QAction("模式2", radio_menu)
        mode2.setCheckable(True)
        mode2.triggered.connect(lambda: self.mode_selected("模式2"))
        action_group.addAction(mode2)
        radio_menu.addAction(mode2)

        mode3 = QAction("模式3", radio_menu)
        mode3.setCheckable(True)
        mode3.triggered.connect(lambda: self.mode_selected("模式3"))
        action_group.addAction(mode3)
        radio_menu.addAction(mode3)

    def mode_selected(self, mode):
        print(f"当前选择: {mode}")

    def quit_app(self):
        self.tray_icon.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    tray = TrayApp()
    tray.run()
