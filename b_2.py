# b_2.py :
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
import a_2
from c_2 import KeyboardThread

class Controller(QObject):
    show_widgets_signal = Signal()

    def __init__(self):
        super().__init__()
        self.show_widgets_signal.connect(self._on_show_widgets)
        self.widget = None

    def _on_show_widgets(self):
        self.widget = a_2.show_widgets()

def run_app():
    app = QApplication(sys.argv)
    controller = Controller()

    # 啟動鍵盤監聽線程
    kb_thread = KeyboardThread()
    kb_thread.trigger.connect(controller.show_widgets_signal.emit)
    kb_thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()



# 问题出在窗口对象被创建后没有被持续引用，导致被 Python 垃圾回收机制销毁，从而出现 “一闪而过” 的现象。具体来说，a_2.show_widgets()创建的窗口对象在_on_show_widgets方法执行结束后就失去了引用，被自动回收了。
# 解决方案：保存窗口对象的引用
# 需要在Controller中保存窗口对象的引用，防止其被垃圾回收。修改b_2.py如下：
# 原理说明：
# 在Controller类中添加了self.widget属性，用于存储a_2.show_widgets()创建的窗口对象。
# 当_on_show_widgets调用时，将窗口对象赋值给self.widget，这样窗口对象就有了持续的引用（被Controller实例持有），不会被垃圾回收。
# 窗口对象得以保留，因此能正常显示，文字也会正确渲染。