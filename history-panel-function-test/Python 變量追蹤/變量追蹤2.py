import inspect

class TrackedVar:
    def __init__(self, value):
        self._value = value

    def __repr__(self):
        frame = inspect.currentframe().f_back
        print(f"[READ] {frame.f_code.co_filename}:{frame.f_lineno}")
        return repr(self._value)

    def set(self, value):
        frame = inspect.currentframe().f_back
        print(f"[WRITE] {frame.f_code.co_filename}:{frame.f_lineno}")
        self._value = value

    def get(self):
        frame = inspect.currentframe().f_back
        print(f"[READ] {frame.f_code.co_filename}:{frame.f_lineno}")
        return self._value

# 初始化一次，全程共享
unpinned_groups = TrackedVar([])
