import keyboard
from PySide6.QtCore import QPoint, Qt, QTimer, Signal, QObject
from PySide6.QtGui import QAction, QFont, QIcon, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
import argparse
import os
import subprocess
import sys
import threading

# 确保 Config 配置正确（核心：suppress=True 且 hold_mode=True）
class Config:
    hold_mode = True
    suppress = True  # 必须为 True，阻止原始单引号输出


speech_recognition_shortcut_test = "p"  # 绑定的快捷键


def hold_mode_A0(event, signal):
    signal.trigger_hold_mode.emit(event)


def click_mode_A0(event, signal):
    signal.trigger_click_mode.emit(event)

class KeyboardHandler(QObject):
    trigger_hold_mode = Signal(keyboard.KeyboardEvent)
    trigger_click_mode = Signal(keyboard.KeyboardEvent)

    def __init__(self):
        super().__init__()
        self.trigger_hold_mode.connect(hold_mode_A)
        self.trigger_click_mode.connect(click_mode_A)
        self.bond_shortcut_history_panel()

    def bond_shortcut_history_panel(self):
        if Config.hold_mode:
            # 关键：确保 suppress=Config.suppress（此时为 True）
            keyboard.hook_key(
                key=speech_recognition_shortcut_test,
                callback=lambda event: hold_mode_A0(event, self),
                suppress=Config.suppress  # 抑制原始按键输出
            )
            print(f"按住模式：快捷键 {speech_recognition_shortcut_test} 已绑定（suppress={Config.suppress}）")
        else:
            keyboard.hook_key(
                key=speech_recognition_shortcut_test,
                callback=lambda event: click_mode_A0(event, self),
                suppress=True
            )
            print(f"单击模式：快捷键 {speech_recognition_shortcut_test} 已绑定")


def hold_mode_A(e: keyboard.KeyboardEvent):
    # # 1. 仅处理首次按下事件（过滤重复的 down 事件）
    # if e.event_type == 'down':
    #     text = "KEY_DOWN"  # 移除空格，确保连续输出
    #     print(f"触发按下：{text}")
    #     keyboard.write(text)  # 输出 KEY_DOWN
    #
    # # 2. 处理抬起事件（仅一次）
    # elif e.event_type == 'up':
    #     text = "KEY_UP"
    #     print(f"触发抬起：{text}")
    #     keyboard.write(text)  # 输出 KEY_UP

    """按下时触发的中文输入逻辑"""
    print(f"type0={e.event_type}")
    if e.event_type == 'down':
        # 按下时：触发输入逻辑（通过信号在主线程执行）
        print(f"type1={e.event_type}")
        text = " DOWN "  # 移除空格，确保连续输出
        #keyboard.write(text)  # 输出 KEY_DOWN
    elif e.event_type == 'up':
        print(f"type2={e.event_type}")
        text = " UP "
        #keyboard.write(text)  # 输出 KEY_UP

def click_mode_A(e: keyboard.KeyboardEvent):
    print(f"触发抬起：")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KeyboardHandler()
    #keyboard.wait()  # 等待热键事件，避免线程退出
    try:
        sys.exit(app.exec())
    finally:
        keyboard.unhook_all()
