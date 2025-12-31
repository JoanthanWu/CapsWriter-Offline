import psutil
from loguru import logger
from util.safe_logger import init_logging


def check_process(name):
    """
    使用psutil检查指定名称的进程是否存在
    """
    try:
        # 将进程名转换为小写以便比较
        target_name = name.lower()

        # 如果输入包含.exe后缀，同时尝试不包含后缀的版本
        search_names = [target_name]
        if target_name.endswith(".exe"):
            search_names.append(target_name[:-4])  # 去除.exe后缀

        # 遍历所有进程
        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = proc.info["name"]
                if proc_name:
                    proc_name_lower = proc_name.lower()
                    # 检查进程名是否匹配任一搜索名
                    for search_name in search_names:
                        if proc_name_lower == search_name:
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # 进程可能已结束或无权访问，跳过
                continue
            except Exception as e:
                # 记录其他异常但不中断循环
                logger.debug(f"检查进程时出现异常: {e}")
                continue

        return False
    except Exception as e:
        init_logging()
        logger.error(f"检查进程时出错: {e}")
        return False


if __name__ == "__main__":
    import time

    now = time.time()
    print(check_process("forhonor.exe"))
    print(time.time() - now)  # 0.01s
