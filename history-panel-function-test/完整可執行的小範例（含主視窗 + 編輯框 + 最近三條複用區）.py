import sys
from collections import deque
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit,
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox
)
from PySide6.QtCore import Qt


class ReuseWidget(QWidget):
    """最近三條複用區"""
    def __init__(self, editor: QTextEdit, recent_texts: deque):
        super().__init__()
        self.editor = editor
        self.recent_texts = recent_texts

        self.combo = QComboBox()
        self.btn_reuse = QPushButton("複用到編輯框")

        layout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.btn_reuse)
        self.setLayout(layout)

        self.btn_reuse.clicked.connect(self.reuse_text)

    def refresh(self):
        """更新下拉選單內容"""
        self.combo.clear()
        self.combo.addItems(list(self.recent_texts))

    def reuse_text(self):
        """將選中的文字插入編輯框"""
        text = self.combo.currentText()
        if text:
            self.editor.insertPlainText(text + "\n")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CapsWriter Demo - 最近三條複用")

        # 主編輯框
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("這裡是主編輯框...")

        # 最近三條快取
        self.recent_texts = deque(maxlen=3)

        # 複用區
        self.reuse_widget = ReuseWidget(self.editor, self.recent_texts)

        # 模擬新增語音轉文字的按鈕
        self.btn_add = QPushButton("模擬新增一條語音文字")
        self.btn_add.clicked.connect(self.add_fake_text)

        # 版面配置
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.reuse_widget)
        right_layout.addWidget(self.btn_add)
        right_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.editor, 3)
        main_layout.addLayout(right_layout, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.counter = 1  # 模擬語音輸入的計數器

    def add_fake_text(self):
        """模擬新增一條語音轉文字"""
        new_text = f"語音轉文字結果 {self.counter}"
        self.counter += 1
        self.recent_texts.append(new_text)
        self.reuse_widget.refresh()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 400)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
