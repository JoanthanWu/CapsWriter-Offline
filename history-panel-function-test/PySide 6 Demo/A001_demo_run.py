# b.py
from PySide6.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
import sys
import A001_demo
def main():
    app = QApplication(sys.argv)
    # 2. 实例化窗口类，创建窗口对象
    window = A001_demo.Mygui()

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
