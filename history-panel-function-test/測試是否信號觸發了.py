from PySide6.QtCore import QObject, Signal

# 1. 槽函数必须在连接前定义（确保作用域可见）
def show_widgets():
    print("===== show_widgets 被触发 =====")
    # （原有逻辑）

# 2. Controller必须继承QObject
class Controller(QObject):
    # 3. 信号必须是类属性（定义在class内部，方法外部）
    show_widgets_signal = Signal()  # 正确的信号定义

# 4. 创建全局唯一实例
controller = Controller()

# 5. 连接信号与槽（此时无需检查数量，直接测试执行）
controller.show_widgets_signal.connect(show_widgets)

# 6. 主动发射信号，测试是否触发槽函数
print("开始测试信号发射...")
controller.show_widgets_signal.emit()  # 发射信号