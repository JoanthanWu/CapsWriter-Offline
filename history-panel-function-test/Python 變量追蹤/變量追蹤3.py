import logging
import inspect

logging.basicConfig(
    filename="tracked.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

class TrackedVar:
    def __init__(self, value):
        self._value = value

    def set(self, value):
        frame = inspect.currentframe().f_back
        logging.info(f"[WRITE] {frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}")
        self._value = value

    def get(self):
        frame = inspect.currentframe().f_back
        logging.info(f"[READ] {frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}")
        return self._value

    def __repr__(self):
        return repr(self.get())

# 初始化一次，全程共享
unpinned_groups = TrackedVar([])
