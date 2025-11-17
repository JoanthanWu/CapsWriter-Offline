import re
import sys
import threading
from pathlib import Path

from loguru import logger


def delete_specific_logs_concise(log_dir: Path):
    """删除符合 *.dddd-dd-dd_dd-dd-dd_dddddd.log 格式的日志文件"""
    pattern = re.compile(r"^.*\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d{6}\.log$")

    # 获取所有匹配的文件
    matching_files = [
        file_path
        for file_path in log_dir.iterdir()
        if file_path.is_file() and pattern.match(file_path.name)
    ]

    # 删除文件
    for file_path in matching_files:
        try:
            file_path.unlink()
            logger.debug(f"已删除: {file_path.name}")
        except Exception as e:
            logger.error(f"删除文件 {file_path.name} 时出错: {e}")

    logger.debug(f"\n总共删除了 {len(matching_files)} 个文件")
    return [f.name for f in matching_files]


class ThreadSafeLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self.log_dir = Path("logs")
            self.setup_logging()
            delete_specific_logs_concise(self.log_dir)
            self._initialized = True

    def get_script_name(self) -> str:
        """从当前执行的 Python 文件名获取脚本名称（不带扩展名）"""
        try:
            # 获取主模块的文件路径
            main_module = sys.modules.get("__main__")
            if (
                main_module
                and hasattr(main_module, "__file__")
                and main_module.__file__
            ):
                script_path = Path(main_module.__file__)
                return script_path.stem  # 返回不带扩展名的文件名
        except (AttributeError, KeyError):
            pass

        # 如果无法获取主模块文件名，尝试其他方法
        try:
            # 尝试从命令行参数获取
            if sys.argv and sys.argv[0]:
                script_path = Path(sys.argv[0])
                return script_path.stem
        except (IndexError, AttributeError):
            pass

        # 最后的手段：使用默认名称
        return "python_script"

    def get_log_file_path(self) -> Path:
        """生成日志文件路径，基于脚本名称"""
        script_name = self.get_script_name()

        # 清理脚本名称，移除可能的不合法文件名字符
        safe_script_name = "".join(
            c for c in script_name if c.isalnum() or c in ("_", "-")
        ).rstrip()
        if not safe_script_name:
            safe_script_name = "python_script"

        return self.log_dir / f"{safe_script_name}.log"

    def setup_logging(self):
        """设置进程安全的日志"""
        # 移除现有处理器
        logger.remove()

        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True)

        # 获取日志文件路径
        log_file = self.get_log_file_path()

        # 文件日志配置
        logger.add(
            sink=str(log_file),
            rotation="10 MB",
            retention="7 days",
            enqueue=True,
            # level="TRACE",
            level="ERROR",
            backtrace=True,
            diagnose=True,
            catch=True,
        )

        # 控制台日志配置
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

        logger.add(
            sink=sys.stderr,
            # level="TRACE",
            level="ERROR",
            catch=True,
        )

        # script_name = self.get_script_name()
        # logger.info(f"日志文件已创建: {log_file.absolute()}")
        # logger.info(f"当前脚本: {script_name}")


# 创建便捷的初始化函数
def init_logging() -> None:
    """初始化日志系统"""
    ThreadSafeLogger()


# 使用方式示例
if __name__ == "__main__":
    # 初始化日志
    init_logging()

    # 正常使用 logger
    logger.info("应用程序启动")

    # 测试不同级别的日志
    logger.debug("调试信息")
    logger.warning("警告信息")
    logger.error("错误信息")
