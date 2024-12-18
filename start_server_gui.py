import sys
import subprocess
from queue import Queue
import threading
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QSystemTrayIcon,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer
from qt_material import apply_stylesheet
from config import ServerConfig as Config
from util.check_process import check_process


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.output_queue_server = Queue()
        self.start_script()

    def init_ui(self):
        self.resize(425, 425)
        self.setWindowTitle("CapsWriter-Offline-Server")
        self.setWindowIcon(QIcon("assets/server-icon.ico"))
        self.create_text_box()
        self.create_clear_button()  # Create clear button
        self.create_systray_icon()
        self.hide()

    def create_text_box(self):
        self.text_box_server = QTextEdit()
        self.text_box_server.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_box_server.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(self.text_box_server)

    def create_clear_button(self):
        # Create a button
        self.clear_button = QPushButton("Clear Server Text", self)

        # Connect click event
        self.clear_button.clicked.connect(lambda: self.clear_text_box())

        # Create a vertical layout
        layout = QVBoxLayout()

        # Add text box and button to the layout
        layout.addWidget(self.text_box_server)
        layout.addWidget(self.clear_button)

        # Create a central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)

        # Set the central widget
        self.setCentralWidget(central_widget)

    def clear_text_box(self):
        # Clear the content of the server text box
        self.text_box_server.clear()

    def create_systray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/server-icon.ico"))
        show_action = QAction("🪟 Show", self)
        quit_action = QAction("❌ Quit", self)

        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        # Minimize to system tray instead of closing the window when the user clicks the close button
        self.hide()  # Hide the window
        event.ignore()  # Ignore the close event

    def quit_app(self):
        # Terminate core_server.py process
        if hasattr(self, "core_server_process") and self.core_server_process:
            self.core_server_process.terminate()
            self.core_server_process.kill()

        # Hide the system tray icon
        self.tray_icon.setVisible(False)

        # Quit the application
        QApplication.quit()

        # TODO: Quit models The above method can not completely exit the model, rename pythonw.exe to pythonw_CapsWriter.exe and taskkill. It's working but not the best way.
        if Config.start_online_translate_server:
            subprocess.Popen(
                "taskkill /IM pythonw_CapsWriter_Server.exe /IM deeplx_windows_amd64.exe /F",
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
            )
        else:
            subprocess.Popen(
                "taskkill /IM pythonw_CapsWriter_Server.exe /F",
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
            )

    def on_tray_icon_activated(self, reason):
        # Called when the system tray icon is activated
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()  # Show the main window

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()  # Press ESC to hide main window

    def start_script(self):
        # Start core_server.py and redirect output to the server queue

        # While Debug error    for line in iter(out.readline, ''):
        # Use this line to replace the original code
        # self.core_server_process = subprocess.Popen(['.\\runtime\\pythonw_CapsWriter_Server.exe', 'core_server.py'], creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')

        self.core_server_process = subprocess.Popen(
            [".\\runtime\\pythonw_CapsWriter_Server.exe", "core_server.py"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        threading.Thread(
            target=self.enqueue_output,
            args=(self.core_server_process.stdout, self.output_queue_server),
            daemon=True,
        ).start()

        # Update text box
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_text_box)
        self.update_timer.start(100)

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b""):
            queue.put(line)

    def update_text_box(self):
        # Update server text box
        while not self.output_queue_server.empty():
            line = self.output_queue_server.get()
            self.text_box_server.append(line)


if __name__ == "__main__":
    if Config.only_run_once and check_process("pythonw_CapsWriter_Server.exe"):
        raise Exception(
            "已经有一个服务端在运行了！（用户配置了 只允许运行一次，禁止多开；而且检测到 pythonw_CapsWriter_Server.exe 进程已在运行。如果你确定需要启动多个服务端同时运行，请先修改 config.py  class ServerConfig:  Only_run_once = False 。）"
        )

    if Config.in_the_meantime_start_the_client and not (
        check_process("start_client_gui.exe")
        or check_process("start_client_gui_admin.exe")
    ):
        # 设置了启动服务端的同时启动客户端且客户端未在运行
        if Config.in_the_meantime_start_the_client_and_run_as_admin:
            # 以用管理员权限启动客户端...
            subprocess.Popen(
                ["start_client_gui_admin.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            # 以用户权限启动客户端...
            subprocess.Popen(
                ["start_client_gui.exe"], creationflags=subprocess.CREATE_NO_WINDOW
            )

    app = QApplication([])
    apply_stylesheet(app, theme="dark_amber.xml")
    gui = GUI()
    if not Config.shrink_automatically_to_tray:
        gui.show()
    sys.exit(app.exec())
