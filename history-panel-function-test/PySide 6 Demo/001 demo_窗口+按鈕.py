import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGroupBox, QFrame, QSizePolicy
)
from PySide6.QtGui import (
    QColor, QFont, QGradient, QLinearGradient, QBrush,
    QPainter, QFontDatabase
)
from PySide6.QtCore import (
    Qt, QSize, QPoint
)


class LayeredStyleDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 多层级样式控制 Demo")
        self.resize(800, 600)

        # ===================== 层级1：顶级窗口设置 =====================
        # 1.1 窗口基础属性
        self.setMinimumSize(600, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)  # 窗口标志
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 启用窗口透明（可选）

        # 1.2 窗口全局样式（最低优先级，可被子控件覆盖）
        self.setStyleSheet("""
            /* 顶级窗口样式（QMainWindow） */
            QMainWindow {
                background-color: rgba(240, 245, 250, 255);  /* 窗口底层背景 */
                border: 2px solid #2c3e50;                   /* 窗口边框 */
                border-radius: 10px;                         /* 窗口圆角 */
            }
        """)

        # ===================== 层级2：中央容器（主布局容器） =====================
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 2.1 中央容器样式（覆盖窗口样式，优先级更高）
        self.central_widget.setStyleSheet("""
            QWidget#central_widget {
                background-color: rgba(220, 230, 240, 200);  /* 半透明背景 */
                padding: 20px;                                /* 内边距 */
                border-radius: 8px;                           /* 容器圆角 */
            }
        """)
        self.central_widget.setObjectName("central_widget")  # 样式表精准匹配

        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # ===================== 层级3：分组容器（功能分组） =====================
        # 3.1 第一组：基础文本层级
        self.text_group = QGroupBox("📝 文本层级控制（QLabel）")
        self.text_group.setStyleSheet("""
            QGroupBox {
                /* 分组框整体样式 */
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;              /* 分组标题文字颜色 */
                background-color: rgba(255, 255, 255, 180);  /* 分组背景 */
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding-top: 15px;           /* 标题与内容间距 */
            }
            QGroupBox::title {
                /* 分组标题单独样式 */
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #e74c3c;              /* 标题文字强调色 */
            }
        """)
        self.main_layout.addWidget(self.text_group)

        # 文本组布局
        text_layout = QVBoxLayout(self.text_group)
        text_layout.setSpacing(10)

        # 3.1.1 层级4：基础文本（继承分组样式）
        self.label_basic = QLabel("基础文本：继承分组样式")
        text_layout.addWidget(self.label_basic)

        # 3.1.2 层级4：自定义文本（覆盖父级样式）
        self.label_custom = QLabel("自定义文本：覆盖父级样式（红色+粗体+居中）")
        self.label_custom.setStyleSheet("""
            QLabel#label_custom {
                color: #e74c3c;              /* 文字颜色 */
                font-size: 16px;
                font-weight: bold;
                text-align: center;          /* 文字居中 */
                background-color: rgba(255, 240, 240, 150);  /* 文本背景 */
                padding: 8px;
                border-radius: 4px;
            }
        """)
        self.label_custom.setObjectName("label_custom")
        self.label_custom.setAlignment(Qt.AlignCenter)  # 代码层面设置对齐
        text_layout.addWidget(self.label_custom)

        # 3.1.3 层级4：富文本（混合样式）
        self.label_rich = QLabel()
        self.label_rich.setText("""
            <p>富文本：<span style="color: #3498db; font-size: 18px;">多色文字</span> 
            <b>粗体</b> <i>斜体</i> <u>下划线</u></p>
            <p>数字：<font color="#27ae60">123456</font></p>
        """)
        self.label_rich.setStyleSheet("""
            QLabel {
                background-color: rgba(240, 255, 240, 150);
                padding: 8px;
                border: 1px dashed #27ae60;
            }
        """)
        text_layout.addWidget(self.label_rich)

        # 3.2 第二组：按钮层级（状态样式）
        self.button_group = QGroupBox("🔘 按钮层级控制（QPushButton）")
        self.button_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #3498db;
            }
        """)
        self.main_layout.addWidget(self.button_group)

        # 按钮组布局
        button_layout = QHBoxLayout(self.button_group)
        button_layout.setSpacing(15)

        # 3.2.1 层级4：普通按钮（基础样式）
        self.btn_normal = QPushButton("普通按钮")
        self.btn_normal.setStyleSheet("""
            QPushButton {
                background-color: #3498db;  /* 正常背景 */
                color: white;               /* 文字颜色 */
                font-size: 14px;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;  /* 悬浮背景 */
            }
            QPushButton:pressed {
                background-color: #1f618d;  /* 按下背景 */
            }
        """)
        button_layout.addWidget(self.btn_normal)

        # 3.2.2 层级4：渐变背景按钮（高级样式）
        self.btn_gradient = QPushButton("渐变背景按钮")
        # 代码层面设置渐变（替代样式表）
        self.btn_gradient.setStyleSheet("""
            QPushButton {
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                /* 线性渐变：从左到右 */
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 #e67e22, stop:1 #d35400);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 #f39c12, stop:1 #e67e22);
            }
        """)
        button_layout.addWidget(self.btn_gradient)

        # ===================== 层级3：自定义绘制容器（最高级控制） =====================
        self.custom_frame = CustomDrawFrame()
        self.custom_frame.setFixedHeight(120)
        self.custom_frame.setStyleSheet("""
            CustomDrawFrame {
                background-color: rgba(255, 255, 255, 100);
                border: 2px solid #8e44ad;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.main_layout.addWidget(self.custom_frame)

        # 自定义容器内的文本（层级5）
        self.frame_label = QLabel("🎨 自定义绘制层（paintEvent 直接绘制）")
        self.frame_label.setStyleSheet("""
            QLabel {
                color: #8e44ad;
                font-size: 16px;
                font-weight: bold;
                background: transparent;  /* 透明背景，透出父容器 */
            }
        """)
        frame_layout = QVBoxLayout(self.custom_frame)
        frame_layout.addWidget(self.frame_label, alignment=Qt.AlignCenter)

    def paintEvent(self, event):
        """
        顶级窗口的 paintEvent（可选）：
        可直接绘制窗口背景（优先级高于样式表）
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制窗口底层渐变（仅当 WA_TranslucentBackground 启用时可见）
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(200, 210, 220, 50))
        gradient.setColorAt(1, QColor(180, 190, 200, 50))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)


# 自定义绘制容器（演示 paintEvent 层级控制）
class CustomDrawFrame(QFrame):
    def paintEvent(self, event):
        """
        自定义绘制：优先级高于样式表，可实现复杂背景/文字
        """
        # 1. 先绘制父类样式（保留样式表效果）
        super().paintEvent(event)

        # 2. 自定义绘制渐变文字背景
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆形渐变背景
        gradient = QLinearGradient(self.rect().center(), self.rect().topRight())
        gradient.setColorAt(0, QColor(142, 68, 173, 30))
        gradient.setColorAt(1, QColor(142, 68, 173, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect().center(), 80, 60)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 全局应用样式（最低优先级，可被所有控件覆盖）
    app.setStyleSheet("""
        /* 全局默认样式 */
        QWidget {
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            font-size: 12px;
        }
        QLabel {
            color: #34495e;  /* 全局文本默认色 */
        }
    """)

    demo = LayeredStyleDemo()
    demo.show()
    sys.exit(app.exec())