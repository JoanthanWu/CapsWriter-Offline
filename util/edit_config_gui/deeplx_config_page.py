from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from rich import print
from rich.console import Console
from rich.table import Table
from siui.components import (
    SiDenseVContainer,
    SiLineEditWithDeletionButton,
    SiTitledWidgetGroup,
)
from siui.components.button import (
    SiLongPressButtonRefactor,
)
from siui.components.option_card import SiOptionCardLinear
from siui.components.page import SiPage
from siui.components.spinbox.spinbox import SiIntSpinBox
from siui.components.titled_widget_group import SiTitledWidgetGroup
from siui.components.widgets import (
    SiDenseVContainer,
)
from siui.core import SiGlobal

from util.edit_config_gui.clearly_type import clearly_type
from util.edit_config_gui.write_toml import write_toml
from util.edit_config_gui.value_check import ValueCheck

from .select_path import SelectPath
from .set_default_button import SetDefaultButton


class DeeplxConfigPage(SiPage):
    def __init__(self, config, config_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.config_path = config_path
        self.deeplx_exe_path: str = self.config["deeplx"]["exe_path"]
        self.init_ui()
        self.deeplx_exe_path_selector.pathSelected.connect(
            self.on_deeplx_exe_path_selected
        )
        self.deeplx_exe_path_selector.path_input.lineEdit().editingFinished.connect(
            lambda: self.on_deeplx_exe_path_selected(
                self.deeplx_exe_path_selector.path_input.lineEdit().text()
            )
        )
        self.online_translate_port_set_default.clicked.connect(
            lambda: self.online_translate_port.setValue(1188)
        )
        self.api_set_default.clicked.connect(
            lambda: self.api.lineEdit().setText("http://127.0.0.1:1188/translate")
        )
        self.save.longPressed.connect(self.save_config)
        # 数据校验绑定
        self.save.clicked.connect(lambda: self.validate_deeplx_exe_path(on_save=True))

    def validate_deeplx_exe_path(self, on_save: bool = False):
        if not on_save:
            if not self.deeplx_exe_path:
                return
        else:
            if not self.deeplx_exe_path:
                try:
                    SiGlobal.siui.windows[
                        "MAIN_WINDOW"
                    ].LayerRightMessageSidebar().send(
                        title="DeepLX 可执行文件 路径不可为空",
                        text="已恢复默认值：deeplx_windows_amd64.exe",
                        msg_type=3,
                        icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                        fold_after=5000,
                    )
                except ValueError:
                    pass
                self.deeplx_exe_path_selector.path_input.lineEdit().setText(
                    "deeplx_windows_amd64.exe"
                )
                self.deeplx_exe_path = "deeplx_windows_amd64.exe"
        is_valid, error = ValueCheck.is_file_exist(self.deeplx_exe_path, ".exe")

        if is_valid:
            print(f"[green]{self.deeplx_exe_path}[/green]")
        else:
            print(f"[red]{self.deeplx_exe_path} - {error if error else '无效'}[/red]")

        if error:
            self.deeplx_exe_path_selector.path_input.lineEdit().setText(
                "deeplx_windows_amd64.exe"
            )
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="DeepLX 可执行文件位置错误",
                    text=f"{self.deeplx_exe_path} - {error}\n已恢复默认值：deeplx_windows_amd64.exe",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def init_ui(self):
        self.setPadding(64)
        self.setScrollMaximumWidth(1000)
        self.setScrollAlignment(Qt.AlignLeft)
        self.setTitle("DeepLX 配置")

        # 创建控件组
        self.titled_widgets_group = SiTitledWidgetGroup(self)
        self.titled_widgets_group.setSpacing(32)
        self.titled_widgets_group.setAdjustWidgetsSize(True)

        # 保存配置按钮
        with self.titled_widgets_group as group:
            self.save = SiLongPressButtonRefactor(self)
            self.save.setSvgIcon(SiGlobal.siui.iconpack.get("ic_fluent_save_filled"))
            self.save.setIconSize(QSize(32, 32))
            self.save.setText("\t保存 DeepLX 配置")
            self.save.setFont(QFont("Microsoft YaHei", 16))
            self.save.setToolTip(
                "点击按钮进行数据格式检查\n长按以确认将数据写入配置文件\n保存配置后请手动重启 服务端/客户端 以加载新配置生效"
            )
            self.save.resize(420, 64)
            self.save_container = SiDenseVContainer(self)
            self.save_container.setAlignment(Qt.AlignCenter)
            self.save_container.addWidget(self.save)
            group.addWidget(self.save_container)

        with self.titled_widgets_group as group:
            group.addTitle("通用")

            # DeepLX 可执行文件路径
            self.deeplx_exe_path_selector = SelectPath(
                self,
                title="DeepLX 可执行文件位置",
                label_text="用于在线翻译",
                default_path=self.config["deeplx"]["exe_path"],
                file_filter="Executables (*.exe)",
                mode="file",
            )

            # DeepLX 在线翻译服务端口
            self.online_translate_port = SiIntSpinBox(group)
            self.online_translate_port.resize(256, 32)
            self.online_translate_port.setMinimum(1024)
            self.online_translate_port.setMaximum(65535)
            self.online_translate_port.setValue(
                int(self.config["deeplx"]["online_translate_port"])
            )
            self.online_translate_port_set_default = SetDefaultButton(self)
            self.online_translate_port_linear_attaching = SiOptionCardLinear(self)
            self.online_translate_port_linear_attaching.setTitle(
                "DeepLX 在线翻译服务端口", '默认值："1188" 端口号范围 1024-65535'
            )
            self.online_translate_port_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.online_translate_port_linear_attaching.addWidget(
                self.online_translate_port_set_default
            )
            self.online_translate_port_linear_attaching.addWidget(
                self.online_translate_port
            )

            # DeepLX API 地址
            self.api = SiLineEditWithDeletionButton(self)
            self.api.lineEdit().setText(self.config["deeplx"]["api"])
            self.api.resize(256, 32)
            self.api_set_default = SetDefaultButton(self)
            self.api_linear_attaching = SiOptionCardLinear(self)
            self.api_linear_attaching.setTitle(
                "DeepLX API 地址", '默认值："http://127.0.0.1:1188/translate"'
            )
            self.api_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.api_linear_attaching.addWidget(self.api_set_default)
            self.api_linear_attaching.addWidget(self.api)

            # 设置项
            self.general_container = SiDenseVContainer(self)
            self.general_container.setFixedWidth(700)
            self.general_container.setAdjustWidgetsSize(True)
            self.general_container.addWidget(self.deeplx_exe_path_selector)
            self.general_container.addWidget(
                self.online_translate_port_linear_attaching
            )
            self.general_container.addWidget(self.api_linear_attaching)
            group.addWidget(self.general_container)

        # 添加页脚的空白以增加美观性
        self.titled_widgets_group.addPlaceholder(64)

        # 设置控件组为页面对象
        self.setAttachment(self.titled_widgets_group)

    def on_deeplx_exe_path_selected(self, path):
        self.deeplx_exe_path = path
        print(f"Deeplx exe path selected: {self.deeplx_exe_path}")
        self.validate_deeplx_exe_path()

    def save_config(self):
        def get_value_from_gui():
            self.config["deeplx"]["exe_path"] = self.deeplx_exe_path
            self.config["deeplx"]["online_translate_port"] = str(
                self.online_translate_port.value()
            )
            self.config["deeplx"]["api"] = self.api.lineEdit().text()

        def print_config():
            console = Console()
            table = Table(title="保存 DeepLX 参数配置")
            table.add_column("属性名", style="cyan")
            table.add_column("类型", style="magenta")
            table.add_column("值", style="green")
            table.add_row(
                "exe_path",
                clearly_type(self.config["deeplx"]["exe_path"]),
                str(self.config["deeplx"]["exe_path"]),
            )
            table.add_row(
                "online_translate_port",
                clearly_type(self.config["deeplx"]["online_translate_port"]),
                str(self.config["deeplx"]["online_translate_port"]),
            )
            table.add_row(
                "api",
                clearly_type(self.config["deeplx"]["api"]),
                str(self.config["deeplx"]["api"]),
            )
            console.print(table)

        try:
            self.save.clicked.emit()
            get_value_from_gui()
            print_config()
            write_toml(self.config, self.config_path)
            SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                "保存 DeepLX 配置成功！\n手动重启服务端和客户端以加载新配置。",
                msg_type=1,
                fold_after=2000,
            )
        except Exception as e:
            SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                f"保存 DeepLX 配置失败！\n错误信息：{e}",
                msg_type=4,
            )
