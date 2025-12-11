class TrackedVar:
    def __init__(self, value):
        self._value = value

    def __repr__(self):
        import inspect
        frame = inspect.currentframe().f_back
        print(f"變量被使用於 {frame.f_code.co_filename}:{frame.f_lineno}")
        return repr(self._value)

    def set(self, value):
        import inspect
        frame = inspect.currentframe().f_back
        print(f"變量被重新賦值於 {frame.f_code.co_filename}:{frame.f_lineno}")
        self._value = value

# 使用
x = TrackedVar([])
x.set([1,2,3])
print(x)
