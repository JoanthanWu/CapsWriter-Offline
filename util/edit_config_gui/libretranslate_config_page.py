from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
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
from siui.components.titled_widget_group import SiTitledWidgetGroup
from siui.components.widgets import (
    SiDenseVContainer,
)
from siui.core import SiGlobal

from util.value_check import ValueCheck

from .set_default_button import SetDefaultButton


class LibretranslateConfigPage(SiPage):
    def __init__(self, config, config_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.config_path = config_path
        self.libretranslate_api: str = self.config["libretranslate"]["api"]
        self.init_ui()

        # 连接信号
        self.api_set_default.clicked.connect(
            lambda: self.api.lineEdit().setText("http://192.168.3.248:5000/")
        )
        self.api.lineEdit().editingFinished.connect(
            lambda: self.on_api_changed(self.api.lineEdit().text())
        )
        self.save.longPressed.connect(self.save_config)
        # 数据校验绑定
        self.save.clicked.connect(lambda: self.validate_api_url(on_save=True))

    def validate_api_url(self, on_save: bool = False):
        if not on_save:
            if not self.libretranslate_api:
                return
        else:
            if not self.libretranslate_api:
                try:
                    SiGlobal.siui.windows[
                        "MAIN_WINDOW"
                    ].LayerRightMessageSidebar().send(
                        title="LibreTranslate API 地址不可为空",
                        text="已恢复默认值：http://192.168.3.248:5000/",
                        msg_type=3,
                        icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                        fold_after=5000,
                    )
                except ValueError:
                    pass
                self.api.lineEdit().setText("http://192.168.3.248:5000/")
                self.libretranslate_api = "http://192.168.3.248:5000/"
                self.validate_api_url()

        # 验证URL格式
        is_valid, error = ValueCheck.is_valid_url(self.libretranslate_api)

        if is_valid:
            print(f"[green]{self.libretranslate_api}[/green]")
        else:
            print(
                f"[red]{self.libretranslate_api} - {error if error else '无效的URL'}[/red]"
            )

        if error:
            self.api.lineEdit().setText("http://192.168.3.248:5000/")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="LibreTranslate API 地址格式错误",
                    text=f"{self.libretranslate_api} - {error}\n已恢复默认值：http://192.168.3.248:5000/",
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
        self.setTitle("LibreTranslate 配置")

        # 创建控件组
        self.titled_widgets_group = SiTitledWidgetGroup(self)
        self.titled_widgets_group.setSpacing(32)
        self.titled_widgets_group.setAdjustWidgetsSize(True)

        # 保存配置按钮
        with self.titled_widgets_group as group:
            self.save = SiLongPressButtonRefactor(self)
            self.save.setSvgIcon(SiGlobal.siui.iconpack.get("ic_fluent_save_filled"))
            self.save.setIconSize(QSize(32, 32))
            self.save.setText("\t保存 LibreTranslate 配置")
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

            # LibreTranslate API 地址
            self.api = SiLineEditWithDeletionButton(self)
            self.api.lineEdit().setText(self.config["libretranslate"]["api"])
            self.api.resize(256, 32)
            self.api_set_default = SetDefaultButton(self)
            self.api_linear_attaching = SiOptionCardLinear(self)
            self.api_linear_attaching.setTitle(
                "LibreTranslate API 地址",
                '默认值："http://192.168.3.248:5000/"\n官方地址："https://libretranslate.com/"（需要API Key）\n建议自行部署：https://github.com/LibreTranslate/LibreTranslate',
            )
            self.api_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.api_linear_attaching.addWidget(self.api_set_default)
            self.api_linear_attaching.addWidget(self.api)

            # 说明文本容器
            self.general_container = SiDenseVContainer(self)
            self.general_container.setFixedWidth(700)
            self.general_container.setAdjustWidgetsSize(True)
            self.general_container.addWidget(self.api_linear_attaching)
            group.addWidget(self.general_container)

        # 添加页脚的空白以增加美观性
        self.titled_widgets_group.addPlaceholder(64)

        # 设置控件组为页面对象
        self.setAttachment(self.titled_widgets_group)

    def on_api_changed(self, api_url):
        self.libretranslate_api = api_url
        print(f"LibreTranslate API changed: {self.libretranslate_api}")
        self.validate_api_url()

    def save_config(self):
        def get_value_from_gui():
            self.config["libretranslate"]["api"] = self.libretranslate_api

        def print_config():
            from rich.console import Console
            from rich.table import Table

            from util.edit_config_gui.clearly_type import clearly_type

            console = Console()
            table = Table(title="保存 LibreTranslate 参数配置")
            table.add_column("属性名", style="cyan")
            table.add_column("类型", style="magenta")
            table.add_column("值", style="green")
            table.add_row(
                "api",
                clearly_type(self.config["libretranslate"]["api"]),
                str(self.config["libretranslate"]["api"]),
            )
            console.print(table)

        from siui.core import SiGlobal

        from util.edit_config_gui.write_toml import write_toml

        try:
            self.save.clicked.emit()
            get_value_from_gui()
            print_config()
            write_toml(self.config, self.config_path)
            SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                "保存 LibreTranslate 配置成功！\n手动重启服务端和客户端以加载新配置。",
                msg_type=1,
                fold_after=2000,
            )
        except Exception as e:
            SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                f"保存 LibreTranslate 配置失败！\n错误信息：{e}",
                msg_type=4,
            )
