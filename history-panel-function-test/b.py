import sys
from PySide6.QtWidgets import QApplication
import a   # 匯入 a.py

def run_demo():
    app = QApplication(sys.argv)
    demo = a.show_widgets()   # 呼叫 a.py 裡的函數
    sys.exit(app.exec())

if __name__ == "__main__":
    run_demo()
