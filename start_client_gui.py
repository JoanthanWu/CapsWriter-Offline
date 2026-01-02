import argparse
import os
import subprocess
import sys
import threading
from pathlib import Path
from queue import Queue

import win32api
import win32con
import win32gui
import win32print
from loguru import logger
from PySide6.QtCore import QFileSystemWatcher, QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QFont, QIcon, QWheelEvent
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
from qt_material import apply_stylesheet
from tomlkit import dumps, parse

from util.check_process import check_process
from util.client.check_microphone_usage import is_microphone_in_use
from util.config import ClientConfig as Config
from util.safe_logger import init_logging


class Hint_While_Recording_At_Cursor_Position(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setVisible(False)  # 初始时隐藏标签

        # 创建一个定时器来定期更新鼠标位置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tooltip_position)
        self.timer.start(100)  # 每100毫秒更新一次

    def update_tooltip_position(self):
        # 使用pywin32获取全局鼠标位置
        x, y = win32api.GetCursorPos()
        global scale_x, scale_y
        x, y = x / scale_x, y / scale_y
        # 更新标签的位置和文本
        self.move(x + (20 / scale_x), y + (20 / scale_y))
        if is_microphone_in_use():
            self.setText(chr(0xF8B1))
            self.setVisible(True)
        else:
            self.setVisible(False)


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_toml_path = Path() / "config.toml"
        self.config_data = None  # 存储配置数据
        self.load_config()  # 初始加载配置
        self.init_ui()
        self.output_queue_client = Queue()
        self.start_script()
        self.edgeMargin = 5  # 侧边停靠残余像素值
        self.isBerthLeft = False
        self.isBerthRight = False

        # 初始化文件系统监控器
        self.init_file_watcher()

    def load_config(self):
        """加载配置文件到内存"""
        try:
            with open(self.config_toml_path, "r", encoding="utf-8") as f:
                config_str = f.read()
                self.config_data = parse(config_str)
            logger.debug("配置文件已加载到内存")
        except Exception as e:
            init_logging()
            logger.error(f"读取配置文件失败: {e}")
            self.config_data = None

    def save_config(self):
        """保存配置数据到文件"""
        try:
            with open(self.config_toml_path, "w", encoding="utf-8") as f:
                f.write(dumps(self.config_data))
            logger.debug("配置已保存到文件")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def get_config_value(self, path: str, default=None):
        """通过点分隔的路径获取配置值"""
        if not self.config_data:
            self.load_config()
            if not self.config_data:
                return default

        try:
            # 使用点分割路径
            keys = path.split(".")
            value = self.config_data

            # 逐层访问嵌套字典
            for key in keys:
                if key in value:
                    value = value[key]
                else:
                    return default
            return value
        except Exception as e:
            logger.error(f"获取配置值失败 [{path}]: {e}")
            return default

    def set_config_value(self, path: str, value):
        """通过点分隔的路径设置配置值"""
        if not self.config_data:
            self.load_config()
            if not self.config_data:
                return False

        try:
            # 使用点分割路径
            keys = path.split(".")
            data = self.config_data

            # 逐层访问嵌套字典，如果不存在则创建
            for i, key in enumerate(keys[:-1]):
                if key not in data:
                    data[key] = {}
                data = data[key]

            # 设置最终的值
            data[keys[-1]] = value
            return True
        except Exception as e:
            logger.error(f"设置配置值失败 [{path}]: {e}")
            return False

    def init_ui(self):
        self.resize(425, 425)
        self.setWindowTitle("CapsWriter-Offline-Client")
        self.setWindowIcon(QIcon("assets/icon/client-icon.ico"))
        self.setWindowOpacity(0.9)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.FramelessWindowHint  # 隐藏标题栏
            | Qt.Tool  # 隐藏Windows任务栏上的图标
            | Qt.WindowStaysOnTopHint  # 置顶
        )
        self.create_stay_on_top_button()
        self.create_cloudypaste_button()  # Create cloudy paste button
        self.create_clear_button()  # Create clear button
        self.create_close_button()
        self.create_custom_title_bar()
        self.create_text_box()
        self.create_monitor_checkbox()  # Create monitor checkbox
        # self.create_stay_on_top_checkbox()
        self.create_wordcount_label()
        self.create_systray_icon()

        # Create a vertical layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)  # 设置控件间距为0像素
        self.layout.setContentsMargins(3, 3, 3, 3)  # 设置左、上、右、下的边距
        self.layout2 = QHBoxLayout()
        self.layout2.setSpacing(0)  # 设置控件间距为0像素
        self.layout2.setContentsMargins(0, 0, 0, 0)  # 设置左、上、右、下的边距为0像素

        # Add text box and button to the layout
        self.layout.addLayout(self.title_bar)
        self.layout.addWidget(self.text_box_client)
        self.layout2.addWidget(self.monitor_checkbox, alignment=Qt.AlignLeft)
        # self.layout2.addWidget(self.stay_on_top_checkbox, alignment=Qt.AlignLeft)
        self.layout2.addSpacerItem(
            QSpacerItem(40, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.layout2.addWidget(self.text_box_wordCountLabel, alignment=Qt.AlignRight)
        self.layout.addLayout(self.layout2)

        # Create a central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        # Set the central widget
        self.setCentralWidget(central_widget)

    def init_file_watcher(self):
        """初始化文件系统监控器"""
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.addPath(str(self.config_toml_path))
        self.file_watcher.fileChanged.connect(self.on_config_file_changed)

        # 使用定时器来防止多次触发
        self.config_update_timer = QTimer()
        self.config_update_timer.setSingleShot(True)
        self.config_update_timer.timeout.connect(self.update_tray_menu_from_config)

    def on_config_file_changed(self, path):
        """当配置文件发生变化时触发"""
        # 重新添加文件监控（因为文件变化时监控可能会失效）
        if not self.file_watcher.files():
            self.file_watcher.addPath(str(self.config_toml_path))

        # 重新加载配置到内存
        self.load_config()

        # 启动定时器，延迟更新，防止多次触发
        self.config_update_timer.start(1000)  # 1秒后更新

    def update_tray_menu_from_config(self):
        """从内存中的配置数据更新托盘菜单"""
        try:
            # 更新保存音频选项
            old_value_save_audio = self.get_config_value("client.save_audio", False)
            match old_value_save_audio:
                case True:
                    self.save_audio_action.setText("✅ 保存音频")
                case False:
                    self.save_audio_action.setText("❌ 保存音频")

            # 更新保存日记选项
            old_value_save_markdown = self.get_config_value(
                "client.save_markdown", False
            )
            match old_value_save_markdown:
                case True:
                    self.save_markdown_action.setText("✅ 保存日记")
                    self.save_non_kwd_markdown_action.setEnabled(True)
                    self.save_non_kwd_markdown_action.setText("⚙️ 保存非关键词日记")
                case False:
                    self.save_markdown_action.setText("❌ 保存日记")
                    self.save_non_kwd_markdown_action.setEnabled(False)
                    self.save_non_kwd_markdown_action.setText("❗ 请先启用保存日记")

            # 更新保存非关键词日记选项
            old_value_save_non_kwd_markdown = self.get_config_value(
                "client.save_non_kwd_markdown", False
            )
            match old_value_save_non_kwd_markdown:
                case True:
                    self.save_non_kwd_markdown_action.setText("✅ 保存非关键词日记")
                case False:
                    self.save_non_kwd_markdown_action.setText("❌ 保存非关键词日记")
            if old_value_save_markdown is False:
                self.save_non_kwd_markdown_action.setEnabled(False)
                self.save_non_kwd_markdown_action.setText("❗ 请先启用保存日记")

            # 更新简繁体转换选项
            old_value_convert_to_traditional_chinese_main = self.get_config_value(
                "client.convert_to_traditional_chinese_main", "简"
            )
            match old_value_convert_to_traditional_chinese_main:
                case "简":
                    self.convert_to_traditional_chinese_main_action.setText("简体中文")
                case "繁":
                    self.convert_to_traditional_chinese_main_action.setText("繁體中文")

            # 更新AI优化语言表达选项
            old_value_enable_ai_optimize_language_expression = self.get_config_value(
                "client.zhipuai.enable_ai_optimize_language_expression", False
            )
            match old_value_enable_ai_optimize_language_expression:
                case True:
                    self.enable_ai_optimize_language_expression_action.setText(
                        "✅ AI 优化语言表达"
                    )
                    self.prompt_style_menu.setEnabled(True)
                case False:
                    self.enable_ai_optimize_language_expression_action.setText(
                        "❌ AI 优化语言表达"
                    )
                    self.prompt_style_menu.setEnabled(False)

            # 更新AI提示风格
            old_value_prompt_style = self.get_config_value(
                "client.zhipuai.prompt_style", "official"
            )
            self.update_prompt_style_menu(old_value_prompt_style)

            logger.debug("托盘菜单已根据配置文件更新")

        except Exception as e:
            logger.error(f"更新托盘菜单失败: {e}")

    def update_prompt_style_menu(self, prompt_style: str):
        """更新提示风格菜单选中状态"""
        # 先取消所有选中状态
        for action in [
            self.prompt_official_action,
            self.prompt_sweetheart_action,
            self.prompt_social_action,
            self.prompt_poetry_action,
            self.prompt_english_action,
            self.prompt_academic_action,
            self.prompt_customer_service_action,
            self.prompt_creative_writing_action,
        ]:
            action.setChecked(False)

        # 根据配置文件设置选中状态
        match prompt_style:
            case "official":
                self.prompt_official_action.setChecked(True)
            case "sweetheart":
                self.prompt_sweetheart_action.setChecked(True)
            case "social":
                self.prompt_social_action.setChecked(True)
            case "poetry":
                self.prompt_poetry_action.setChecked(True)
            case "english":
                self.prompt_english_action.setChecked(True)
            case "academic":
                self.prompt_academic_action.setChecked(True)
            case "customer_service":
                self.prompt_customer_service_action.setChecked(True)
            case "creative_writing":
                self.prompt_creative_writing_action.setChecked(True)
            case _:
                logger.warning(f"不支持的 AI 提示风格：{prompt_style}")

    def create_custom_title_bar(self):
        # 创建自定义标题栏
        self.title_bar = QHBoxLayout()
        self.title_bar.addWidget(self.stay_on_top_button)
        self.title = QLabel("CapsWriter-Offline-Client")
        font = QFont()
        font.setBold(True)
        self.title.setFont(font)
        self.title_bar.addWidget(self.title)
        self.title_bar.addSpacerItem(
            QSpacerItem(80, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.title_bar.addWidget(self.cloudypaste_button, alignment=Qt.AlignRight)
        self.title_bar.addWidget(self.clear_button, alignment=Qt.AlignRight)
        self.title_bar.addWidget(self.close_button)

    def create_stay_on_top_button(self):
        self.stay_on_top_button = QPushButton()
        pin_char = chr(0xE840)
        self.stay_on_top_button.setText(pin_char)
        self.stay_on_top_button.setToolTip("置顶窗口，将它显示在其他窗口之上 / 不置顶")
        self.stay_on_top_button.setMaximumSize(50, 50)
        self.stay_on_top_button.clicked.connect(self.window_stay_on_top_toggled)

    def create_close_button(self):
        self.close_button = QPushButton(chr(0xE8BB))
        self.close_button.setMaximumSize(50, 50)
        self.close_button.clicked.connect(self.hide)

    def create_text_box(self):
        self.text_box_client = QTextEdit()
        self.text_box_client.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_box_client.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def create_monitor_checkbox(self):
        # 创建一个QCheckBox控件
        self.monitor_checkbox = QCheckBox("监听")
        self.monitor_checkbox.setToolTip("监听客户端输出 / 不监听，仅用作笔记本")
        self.monitor_checkbox.setMaximumSize(65, 30)
        # 当状态改变时，调用self.on_monitor_toggled函数
        self.monitor_checkbox.stateChanged.connect(self.on_monitor_toggled)
        # 设置默认状态
        self.monitor_checkbox.setChecked(True)

    def create_wordcount_label(self):
        self.text_box_wordCountLabel = QLabel("字符数字节数", self)
        self.text_box_wordCountLabel.setToolTip("光标已选中字符数 / 总字符数 | 字节数")
        self.text_box_wordCountLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.text_box_client.textChanged.connect(self.update_word_count_toggled)
        self.text_box_client.selectionChanged.connect(self.update_word_count_toggled)

    def create_cloudypaste_button(self):
        self.cloudypaste_button = QPushButton(chr(0xE753), self)
        self.cloudypaste_button.setToolTip(
            "将文本上传至云剪切板，方便向ios设备分享。基于 share.lanol.cn ，一个无依赖即用即走的剪切板。"
        )
        self.cloudypaste_button.setMaximumSize(80, 30)
        self.cloudypaste_button.clicked.connect(self.cloudy_paste)

    def create_clear_button(self):
        # Create a button
        self.clear_button = QPushButton(chr(0xE75C), self)
        self.clear_button.setToolTip("清空文本框中的全部内容")
        self.clear_button.setMaximumSize(80, 30)
        # Connect click event
        self.clear_button.clicked.connect(lambda: self.clear_text_box())

    def create_systray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/icon/client-icon.ico"))
        edit_hot_en_action = QAction("Edit hot-en.txt", self)
        edit_hot_rule_action = QAction("Edit hot-rule.txt", self)
        edit_hot_zh_action = QAction("Edit hot-zh.txt", self)
        edit_keyword_action = QAction("Edit keywords.txt", self)

        explore_home_folder_action = QAction("📁 Open Home Folder With Explorer", self)
        vscode_home_folder_action = QAction("🤓 Open Home Folder With VSCode", self)
        chatglm_website_action = QAction("🤖 ChatGLM Website", self)

        self.save_audio_action = QAction("⚙️ 保存音频", self)
        self.save_markdown_action = QAction("⚙️ 保存日记", self)
        self.save_non_kwd_markdown_action = QAction("⚙️ 保存非关键词日记", self)
        self.convert_to_traditional_chinese_main_action = QAction(
            "⚙️ 默认使用 简/繁 体", self
        )
        self.enable_ai_optimize_language_expression_action = QAction(
            "⚙️ AI 优化语言表达", self
        )

        # 从内存配置中获取当前值
        old_value_save_audio = self.get_config_value("client.save_audio", False)
        old_value_save_markdown = self.get_config_value("client.save_markdown", False)
        old_value_save_non_kwd_markdown = self.get_config_value(
            "client.save_non_kwd_markdown", False
        )
        old_value_convert_to_traditional_chinese_main = self.get_config_value(
            "client.convert_to_traditional_chinese_main", "简"
        )
        old_value_enable_ai_optimize_language_expression = self.get_config_value(
            "client.zhipuai.enable_ai_optimize_language_expression", False
        )
        old_value_prompt_style = self.get_config_value(
            "client.zhipuai.prompt_style", "official"
        )

        match old_value_save_audio:
            case True:
                self.save_audio_action.setText("✅ 保存音频")
            case False:
                self.save_audio_action.setText("❌ 保存音频")
        match old_value_save_markdown:
            case True:
                self.save_markdown_action.setText("✅ 保存日记")
            case False:
                self.save_markdown_action.setText("❌ 保存日记")
        match old_value_save_non_kwd_markdown:
            case True:
                self.save_non_kwd_markdown_action.setText("✅ 保存非关键词日记")
            case False:
                self.save_non_kwd_markdown_action.setText("❌ 保存非关键词日记")
        if old_value_save_markdown is False:
            self.save_non_kwd_markdown_action.setEnabled(False)
            self.save_non_kwd_markdown_action.setText("❗ 请先启用保存日记")
        match old_value_convert_to_traditional_chinese_main:
            case "简":
                self.convert_to_traditional_chinese_main_action.setText("简体中文")
            case "繁":
                self.convert_to_traditional_chinese_main_action.setText("繁體中文")
        match old_value_enable_ai_optimize_language_expression:
            case True:
                self.enable_ai_optimize_language_expression_action.setText(
                    "✅ AI 优化语言表达"
                )
            case False:
                self.enable_ai_optimize_language_expression_action.setText(
                    "❌ AI 优化语言表达"
                )

        self.prompt_style = old_value_prompt_style

        github_website_action = QAction("🌐 GitHub Website", self)
        show_action = QAction("🪟 Show", self)
        restart_client_action = QAction("🔄 Restart Client", self)
        quit_action = QAction("❌ Quit", self)

        edit_hot_en_action.triggered.connect(self.edit_hot_en)
        edit_hot_rule_action.triggered.connect(self.edit_hot_rule)
        edit_hot_zh_action.triggered.connect(self.edit_hot_zh)
        edit_keyword_action.triggered.connect(self.edit_keyword)

        explore_home_folder_action.triggered.connect(self.explore_home_folder)
        vscode_home_folder_action.triggered.connect(self.vscode_home_folder)
        chatglm_website_action.triggered.connect(self.open_chatglm_website)

        self.save_audio_action.triggered.connect(self.toogle_save_audio)
        self.save_markdown_action.triggered.connect(self.toogle_save_markdown)
        self.save_non_kwd_markdown_action.triggered.connect(
            self.toogle_save_non_kwd_markdown
        )
        self.convert_to_traditional_chinese_main_action.triggered.connect(
            self.switch_between_simplified_and_traditional
        )
        self.enable_ai_optimize_language_expression_action.triggered.connect(
            self.toogle_ai_optimize_language_expression
        )
        github_website_action.triggered.connect(self.open_github_website)
        show_action.triggered.connect(self.showNormal)
        restart_client_action.triggered.connect(self.restart_client)
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        tray_menu = QMenu()
        edit_menu = QMenu("📝 Edit Hot Rules", tray_menu)
        view_menu = QMenu("👁️ View", tray_menu)

        edit_menu.addAction(edit_hot_en_action)
        edit_menu.addAction(edit_hot_rule_action)
        edit_menu.addAction(edit_hot_zh_action)
        edit_menu.addAction(edit_keyword_action)

        view_menu.addAction(explore_home_folder_action)
        view_menu.addAction(vscode_home_folder_action)
        view_menu.addAction(chatglm_website_action)

        self.create_prompt_style_submenu(tray_menu)

        tray_menu.addMenu(edit_menu)
        tray_menu.addMenu(view_menu)
        tray_menu.addSeparator()
        tray_menu.addAction(self.save_audio_action)
        tray_menu.addAction(self.save_markdown_action)
        tray_menu.addAction(self.save_non_kwd_markdown_action)
        tray_menu.addAction(self.convert_to_traditional_chinese_main_action)
        tray_menu.addAction(self.enable_ai_optimize_language_expression_action)
        tray_menu.addMenu(self.prompt_style_menu)
        tray_menu.addSeparator()
        tray_menu.addAction(github_website_action)
        tray_menu.addSeparator()
        tray_menu.addAction(show_action)
        tray_menu.addAction(restart_client_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def create_prompt_style_submenu(self, tray_menu: QMenu) -> QMenu:
        self.prompt_style_menu = QMenu("🤖 AI 优化风格", tray_menu)
        if (
            self.enable_ai_optimize_language_expression_action.text()
            == "❌ AI 优化语言表达"
        ):
            self.prompt_style_menu.setDisabled(True)
        else:
            self.prompt_style_menu.setEnabled(True)
        prompt_style_group = QActionGroup(self.prompt_style_menu)
        prompt_style_group.setExclusive(True)

        self.prompt_official_action = QAction("正式公文", self.prompt_style_menu)
        self.prompt_sweetheart_action = QAction("甜言蜜语", self.prompt_style_menu)
        self.prompt_social_action = QAction("社媒文案", self.prompt_style_menu)
        self.prompt_poetry_action = QAction("赋诗一首", self.prompt_style_menu)
        self.prompt_english_action = QAction("英语大师", self.prompt_style_menu)
        self.prompt_academic_action = QAction("学术论文", self.prompt_style_menu)
        self.prompt_customer_service_action = QAction(
            "客户服务", self.prompt_style_menu
        )
        self.prompt_creative_writing_action = QAction(
            "创意写作", self.prompt_style_menu
        )

        self.prompt_official_action.setCheckable(True)
        self.prompt_sweetheart_action.setCheckable(True)
        self.prompt_social_action.setCheckable(True)
        self.prompt_poetry_action.setCheckable(True)
        self.prompt_english_action.setCheckable(True)
        self.prompt_academic_action.setCheckable(True)
        self.prompt_customer_service_action.setCheckable(True)
        self.prompt_creative_writing_action.setCheckable(True)

        self.prompt_official_action.triggered.connect(self.switch_prompt_style)
        self.prompt_sweetheart_action.triggered.connect(self.switch_prompt_style)
        self.prompt_social_action.triggered.connect(self.switch_prompt_style)
        self.prompt_poetry_action.triggered.connect(self.switch_prompt_style)
        self.prompt_english_action.triggered.connect(self.switch_prompt_style)
        self.prompt_academic_action.triggered.connect(self.switch_prompt_style)
        self.prompt_customer_service_action.triggered.connect(self.switch_prompt_style)
        self.prompt_creative_writing_action.triggered.connect(self.switch_prompt_style)

        prompt_style_group.addAction(self.prompt_official_action)
        prompt_style_group.addAction(self.prompt_sweetheart_action)
        prompt_style_group.addAction(self.prompt_social_action)
        prompt_style_group.addAction(self.prompt_poetry_action)
        prompt_style_group.addAction(self.prompt_english_action)
        prompt_style_group.addAction(self.prompt_academic_action)
        prompt_style_group.addAction(self.prompt_customer_service_action)
        prompt_style_group.addAction(self.prompt_creative_writing_action)

        self.prompt_style_menu.addAction(self.prompt_official_action)
        self.prompt_style_menu.addAction(self.prompt_sweetheart_action)
        self.prompt_style_menu.addAction(self.prompt_social_action)
        self.prompt_style_menu.addAction(self.prompt_poetry_action)
        self.prompt_style_menu.addAction(self.prompt_english_action)
        self.prompt_style_menu.addAction(self.prompt_academic_action)
        self.prompt_style_menu.addAction(self.prompt_customer_service_action)
        self.prompt_style_menu.addAction(self.prompt_creative_writing_action)

        self.update_prompt_style_menu(self.prompt_style)

    def toogle_save_audio(self):
        # 从内存配置中获取当前值
        old_value = self.get_config_value("client.save_audio", False)
        # 切换值
        new_value = not old_value
        # 更新内存配置并保存到文件
        if self.set_config_value("client.save_audio", new_value):
            if self.save_config():
                # 更新托盘菜单
                if old_value:
                    self.save_audio_action.setText("❌ 保存音频")
                else:
                    self.save_audio_action.setText("✅ 保存音频")
            else:
                logger.error("保存配置文件失败")
        else:
            logger.error("更新内存配置失败")

    def toogle_save_markdown(self):
        # 从内存配置中获取当前值
        old_value = self.get_config_value("client.save_markdown", False)
        # 切换值
        new_value = not old_value
        # 更新内存配置并保存到文件
        if self.set_config_value("client.save_markdown", new_value):
            if self.save_config():
                # 更新托盘菜单
                if old_value:
                    self.save_markdown_action.setText("❌ 保存日记")
                    self.save_non_kwd_markdown_action.setText("❗ 请先启用保存日记")
                    self.save_non_kwd_markdown_action.setEnabled(False)
                else:
                    self.save_markdown_action.setText("✅ 保存日记")
                    self.save_non_kwd_markdown_action.setText("⚙️ 保存非关键词日记")
                    self.save_non_kwd_markdown_action.setEnabled(True)
                    self.update_save_non_kwd_markdown()
            else:
                logger.error("保存配置文件失败")
        else:
            logger.error("更新内存配置失败")

    def toogle_save_non_kwd_markdown(self):
        # 从内存配置中获取当前值
        old_value = self.get_config_value("client.save_non_kwd_markdown", False)
        # 切换值
        new_value = not old_value
        # 更新内存配置并保存到文件
        if self.set_config_value("client.save_non_kwd_markdown", new_value):
            if self.save_config():
                # 更新托盘菜单
                if old_value:
                    self.save_non_kwd_markdown_action.setText("❌ 保存非关键词日记")
                else:
                    self.save_non_kwd_markdown_action.setText("✅ 保存非关键词日记")
            else:
                logger.error("保存配置文件失败")
        else:
            logger.error("更新内存配置失败")

    def update_save_non_kwd_markdown(self):
        try:
            old_value = self.get_config_value("client.save_non_kwd_markdown", False)
            if old_value:
                self.save_non_kwd_markdown_action.setText("✅ 保存非关键词日记")
            else:
                self.save_non_kwd_markdown_action.setText("❌ 保存非关键词日记")
        except Exception as e:
            init_logging()
            logger.error(f"更新托盘菜单失败: {e}")

    def switch_between_simplified_and_traditional(self):
        # 从内存配置中获取当前值
        old_value = self.get_config_value(
            "client.convert_to_traditional_chinese_main", "简"
        )
        # 切换值
        match old_value:
            case "简":
                new_value = "繁"
            case "繁":
                new_value = "简"
            case _:
                new_value = "简"
        # 更新内存配置并保存到文件
        if self.set_config_value(
            "client.convert_to_traditional_chinese_main", new_value
        ):
            if self.save_config():
                # 更新托盘菜单
                match old_value:
                    case "简":
                        self.convert_to_traditional_chinese_main_action.setText(
                            "繁體中文"
                        )
                    case "繁":
                        self.convert_to_traditional_chinese_main_action.setText(
                            "简体中文"
                        )
            else:
                logger.error("保存配置文件失败")
        else:
            logger.error("更新内存配置失败")

    def toogle_ai_optimize_language_expression(self):
        # 从内存配置中获取当前值
        old_value = self.get_config_value(
            "client.zhipuai.enable_ai_optimize_language_expression", False
        )
        # 切换值
        new_value = not old_value
        # 更新内存配置并保存到文件
        if self.set_config_value(
            "client.zhipuai.enable_ai_optimize_language_expression", new_value
        ):
            if self.save_config():
                # 更新托盘菜单
                if old_value:
                    self.enable_ai_optimize_language_expression_action.setText(
                        "❌ AI 优化语言表达"
                    )
                    self.prompt_style_menu.setDisabled(True)
                    self.prompt_style_menu.setTitle("❗ 请先启用AI优化语言表达")
                else:
                    self.enable_ai_optimize_language_expression_action.setText(
                        "✅ AI 优化语言表达"
                    )
                    self.prompt_style_menu.setEnabled(True)
                    self.prompt_style_menu.setTitle("🤖 AI 优化风格")
            else:
                logger.error("保存配置文件失败")
        else:
            logger.error("更新内存配置失败")

    def switch_prompt_style(self):
        # 获取新值
        new_value: str = ""
        if self.prompt_official_action.isChecked():
            new_value = "official"
        elif self.prompt_sweetheart_action.isChecked():
            new_value = "sweetheart"
        elif self.prompt_social_action.isChecked():
            new_value = "social"
        elif self.prompt_poetry_action.isChecked():
            new_value = "poetry"
        elif self.prompt_english_action.isChecked():
            new_value = "english"
        elif self.prompt_academic_action.isChecked():
            new_value = "academic"
        elif self.prompt_customer_service_action.isChecked():
            new_value = "customer_service"
        elif self.prompt_creative_writing_action.isChecked():
            new_value = "creative_writing"
        else:
            new_value = ""

        # 更新内存配置并保存到文件
        if self.set_config_value("client.zhipuai.prompt_style", new_value):
            if not self.save_config():
                logger.error("保存配置文件失败")
        else:
            logger.error("更新内存配置失败")

    def restart_client(self):
        subprocess.Popen(
            [".\\runtime\\python.exe", ".\\util\\client\\restart.py"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding="utf-8",
        )

    def cloudy_paste(self):
        text = self.text_box_client.toPlainText()
        subprocess.Popen(
            [
                ".\\runtime\\pythonw.exe",
                ".\\util\\client\\cloud_clipboard_show_qrcode.py",
                text,
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding="utf-8",
        )

    def clear_text_box(self):
        # Clear the content of the client text box
        self.text_box_client.clear()
        # Resize Window
        self.resize(425, 425)

    def on_monitor_toggled(self, state):
        # 检查复选框的选中状态
        try:
            if state == 2:  # 2 表示选中状态
                self.update_timer.start(100)
            else:
                self.update_timer.stop()
        except AttributeError:
            pass  # 'GUI' object has no attribute 'update_timer' # 忽略该错误，因为初始化时还没有创建update_timer

    def window_stay_on_top_toggled(self):
        # 切换窗口置顶状态
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            global gui
        window_is_on_top = bool(gui.windowFlags() & Qt.WindowStaysOnTopHint)
        if window_is_on_top:
            pin_char = chr(0xE840)
            self.stay_on_top_button.setText(pin_char)
        else:
            unpin_char = " "
            self.stay_on_top_button.setText(unpin_char)
        self.show()  # 重新显示窗口以应用更改

    def update_word_count_toggled(self):
        select_text_count = len(self.text_box_client.textCursor().selectedText())
        select_text_bytes = len(
            self.text_box_client.textCursor().selectedText().encode("utf-8")
        )
        total_text_count = len(self.text_box_client.toPlainText())
        total_text_bytes = len(self.text_box_client.toPlainText().encode("utf-8"))
        unselect_text_count = total_text_count - select_text_count
        unselect_text_bytes = total_text_bytes - select_text_bytes
        self.text_box_wordCountLabel.setText(
            f"{select_text_count} + {unselect_text_count} = {total_text_count} Words |  {select_text_bytes} + {unselect_text_bytes} = {total_text_bytes} Bytes"
        )
        if total_text_count > 10000:  # 字符数过多时自动清空
            self.text_box_client.clear()

    def edit_hot_en(self):
        os.startfile("hot-en.txt")

    def edit_hot_rule(self):
        os.startfile("hot-rule.txt")

    def edit_hot_zh(self):
        os.startfile("hot-zh.txt")

    def edit_keyword(self):
        os.startfile("keywords.txt")

    def explore_home_folder(self):
        current_directory = os.getcwd()
        os.startfile(current_directory)

    def vscode_home_folder(self):
        current_directory = os.getcwd()
        vscode_exe_path = Config.vscode_exe_path
        subprocess.Popen([vscode_exe_path, current_directory])

    def open_chatglm_website(self):
        os.system("start https://chatglm.cn/main/alltoolsdetail")

    def open_github_website(self):
        os.system("start https://github.com/H1DDENADM1N/CapsWriter-Offline")

    def closeEvent(self, event):
        # Minimize to system tray instead of closing the window when the user clicks the close button
        self.hide()  # Hide the window
        event.ignore()  # Ignore the close event

    def quit_app(self):
        init_logging()

        # Terminate core_client.py process
        if hasattr(self, "core_client_process") and self.core_client_process:
            self.core_client_process.terminate()
            self.core_client_process.kill()

        # 停止文件监控器
        if hasattr(self, "file_watcher"):
            self.file_watcher.removePaths(self.file_watcher.files())
            self.config_update_timer.stop()

        # Hide the system tray icon
        self.tray_icon.setVisible(False)

        # Quit the application
        QApplication.quit()

        # TODO: Quit models The above method can not completely exit the model, rename pythonw.exe to pythonw_CapsWriter.exe and taskkill. It's working but not the best way.
        try:
            proc = subprocess.Popen(
                "taskkill /IM start_client_gui_admin.exe /IM start_client_gui.exe /IM python_CapsWriter_Client.exe /IM hint_while_recording.exe /F",
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
            )
            stdout, stderr = proc.communicate()
            logger.debug(f"Taskkill output: {stdout}")
            if stderr:
                logger.error(f"Taskkill errors: {stderr}")
        except Exception as e:
            logger.error(f"Error occurred while quitting the application: {e}")

    def on_tray_icon_activated(self, reason):
        # Called when the system tray icon is activated
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()  # Show the main window

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()  # Press ESC to hide main window

    def start_script(self):
        # Start core_client.py and redirect output to the client queue
        self.core_client_process = subprocess.Popen(
            [".\\runtime\\python_CapsWriter_Client.exe", "core_client.py"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding="utf-8",
            errors="replace",
        )
        threading.Thread(
            target=self.enqueue_output,
            args=(self.core_client_process.stdout, self.output_queue_client),
            daemon=True,
        ).start()

        # Update text box
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_text_box)
        self.update_timer.start(100)

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, ""):
            line = line.strip()
            queue.put(line)

    def update_text_box(self):
        # Update client text box
        while not self.output_queue_client.empty():
            try:
                line = self.output_queue_client.get()
                self.text_box_client.append(line)
            except Exception as e:
                self.text_box_client.append(e)
                break

    def checkWindowActive(self):
        # 检查窗口是否处于活跃状态
        if self.isActiveWindow():
            pass
        else:
            x, y, width, height, screenWidth, screenHeight = self.checkWindowInfo()
            if x == 0:  # 窗口非活跃状态，从左边弹出的，恢复继续停靠在左边
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif (
                x == screenWidth - width
            ):  # 窗口非活跃状态，从右边弹出的，恢复继续停靠在右边
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            else:
                init_logging()
                logger.debug("窗口无需恢复停靠")
                pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def enterEvent(self, event):
        super().enterEvent(event)
        for i in range(self.title_bar.count()):  # 鼠标进入时显示标题栏
            widget = self.title_bar.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(True)
        for i in range(self.layout2.count()):  # 鼠标进入时显示操作栏
            widget = self.layout2.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(True)
        x, y, width, height, screenWidth, screenHeight = self.checkWindowInfo()
        if self.isBerthLeft:  # 已停靠在左边
            self.move(0, y)  # 从左边弹出，31是标题栏高度
            self.isBerthLeft = False
        elif self.isBerthRight:  # 已停靠在右边
            self.move(screenWidth - width, y)  # 从右边弹出，31是标题栏高度
            self.isBerthRight = False
        else:
            # print("窗口未停靠")
            pass

    def leaveEvent(self, event):
        super().leaveEvent(event)
        for i in range(self.title_bar.count()):  # 鼠标离开时隐藏标题栏
            widget = self.title_bar.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(False)
        for i in range(self.layout2.count()):  # 鼠标离开时隐藏操作栏
            widget = self.layout2.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(False)
        x, y, width, height, screenWidth, screenHeight = self.checkWindowInfo()
        # print(f"左右，高低，宽，高，屏宽，屏高: {(x, y, width, height, screenWidth, screenHeight)}")
        if self.isActiveWindow():  # 窗口活跃状态，用户点击了窗口，则不恢复继续停靠
            # print("窗口活跃状态")
            if x < 0 - width / 2:
                # print("活跃状态，但是窗口的一半已超出屏幕左边界，将窗口停靠在左边")
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif x > screenWidth - width / 2:
                # print("窗口活跃状态，但是窗口的一半已超出屏幕右边界，将窗口停靠在右边")
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            else:
                # print("窗口活跃状态，无需停靠")
                pass
        else:  # 窗口非活跃状态，用户可能只是鼠标划过看一眼，失去焦点时恢复继续停靠
            # print("窗口不活跃状态")
            if x < 0 - width / 2:
                # print("窗口的一半已超出屏幕左边界")
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif x > screenWidth - width / 2:
                # print("窗口的一半已超出屏幕右边界")
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            elif x == 0:  # 窗口非活跃状态，从左边弹出的，恢复继续停靠在左边
                self.berthToLeft(x, y, width, height, screenWidth, screenHeight)
            elif (
                x == screenWidth - width
            ):  # 窗口非活跃状态，从右边弹出的，恢复继续停靠在右边
                self.berthToRight(x, y, width, height, screenWidth, screenHeight)
            else:
                # print("窗口未超出屏幕边界")
                pass

    def berthToLeft(self, x, y, width, height, screenWidth, screenHeight):
        self.move(0 - width + self.edgeMargin, y)  # 停靠到左边，31是标题栏高度
        self.isBerthLeft = True

    def berthToRight(self, x, y, width, height, screenWidth, screenHeight):
        self.move(screenWidth - self.edgeMargin, y)  # 停靠到右边，31是标题栏高度
        self.isBerthRight = True

    def checkWindowInfo(self):
        geometry = self.geometry()
        x = geometry.x()
        y = geometry.y()
        width = geometry.width()
        height = geometry.height()
        primaryScreen = QApplication.instance().primaryScreen()
        screenRect = primaryScreen.geometry()
        screenWidth = screenRect.width()
        screenHeight = screenRect.height()
        return x, y, width, height, screenWidth, screenHeight

    def wheelEvent(self, event: QWheelEvent):
        # 设置初始缩放因子
        self.scale_factor = 1.0
        # 设置缩放因子的最小和最大值
        self.min_scale = 0.5
        self.max_scale = 2.0
        # 检测Ctrl键是否被按下
        if event.modifiers() == Qt.ControlModifier:
            # 计算缩放因子
            # print(event.angleDelta().y())
            if event.angleDelta().y() > 0:
                self.scale_factor *= 1.1  # 放大
            elif event.angleDelta().y() < 0:
                self.scale_factor *= 0.9  # 缩小
            # 限制缩放因子的范围
            self.scale_factor = max(
                self.min_scale, min(self.max_scale, self.scale_factor)
            )
            # 应用缩放因子到所有控件
            self.apply_scale_factor()
        else:
            super().wheelEvent(event)

    def apply_scale_factor(self):
        # 应用缩放因子
        for widget in [self.text_box_client]:
            # 检查字体大小是否已设置，如果没有设置，则使用一个默认值
            current_font = widget.font()
            if current_font.pointSizeF() < 9:
                current_font.setPointSizeF(9)  # 设置一个默认字体大小
            current_font.setPointSizeF(current_font.pointSizeF() * self.scale_factor)
            widget.setFont(current_font)


def start_client_gui():
    Print_Screen_Scale()
    if Config.only_run_once and check_process("python_CapsWriter_Client.exe"):
        raise Exception(
            "已经有一个客户端在运行了！（用户配置了 只允许运行一次，禁止多开；而且检测到 python_CapsWriter_Client.exe 进程已在运行。如果你确定需要启动多个客户端同时运行，请先修改 config.py  class ClientConfig:  Only_run_once = False 。）"
        )
    if (
        Config.hint_while_recording_at_edit_position_powered_by_ahk
        and not check_process("hint_while_recording.exe")
        and Path("hint_while_recording.exe").exists()
        # and Config.hold_mode
    ):
        subprocess.Popen(
            ["hint_while_recording.exe"], creationflags=subprocess.CREATE_NO_WINDOW
        )
    app = QApplication(sys.argv)
    if Config.hint_while_recording_at_cursor_position:
        tooltip = Hint_While_Recording_At_Cursor_Position()
        tooltip.show()
    apply_stylesheet(
        app, theme="dark_teal.xml", css_file="util\\client\\gui_theme_custom.css"
    )
    global gui
    gui = GUI()
    if not Config.shrink_automatically_to_tray:
        gui.show()
    sys.exit(app.exec())


def Print_Screen_Scale():
    init_logging()
    # 获取屏幕的宽度和高度
    hDC = win32gui.GetDC(0)
    screen_width = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    screen_height = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    print(f"屏幕尺寸: {screen_width}x{screen_height}")
    logger.debug(f"屏幕尺寸: {screen_width}x{screen_height}")
    # 获取逻辑的宽度和高度
    logical_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    logical_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    print(f"逻辑尺寸: {logical_width}x{logical_height}")
    logger.debug(f"逻辑尺寸: {logical_width}x{logical_height}")
    # 计算缩放比例
    global scale_x, scale_y
    scale_x = screen_width / logical_width
    scale_y = screen_height / logical_height
    print(f"屏幕缩放比例: {scale_x}, {scale_y}")
    logger.debug(f"屏幕缩放比例: {scale_x}, {scale_y}")


def read_file_list(file_list_path: Path):
    """读取文件列表文件，返回文件路径列表"""
    with open(file_list_path, "r", encoding="utf-8") as f:
        return [Path(line.strip()) for line in f if line.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="处理文件")
    parser.add_argument("files", nargs="*", type=Path, help="要处理的文件")
    parser.add_argument("--file-list", type=Path, help="包含文件列表的文本文件")
    args = parser.parse_args()

    if args.file_list:  # 如果传递了 --file-list 参数
        try:
            files = read_file_list(args.file_list)
        except Exception as e:
            init_logging()
            logger.error(f"读取文件列表失败: {e}")
            sys.exit(1)
    else:
        files = args.files  # 直接传递的文件列表

    if files:  # 如果有文件需要处理
        CapsWriter_path = Path(__file__).parent
        script_path = CapsWriter_path / "core_client.py"
        python_exe_path = CapsWriter_path / "runtime" / "python.exe"
        files_quoted = [str(file) for file in files]
        command = [str(python_exe_path), str(script_path)] + files_quoted
        try:
            subprocess.Popen(command, cwd=str(CapsWriter_path))
        except Exception as e:
            init_logging()
            logger.error(f"启动进程失败: {e}")
    else:
        # GUI
        start_client_gui()
