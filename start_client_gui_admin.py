"""

这个文件 被 start_client_gui_admin.exe 调用

用于实现 以管理员权限运行客户端

当某程序以管理员权限运行
可能会出现有识别结果但是却无法在那个程序输入文字的状况
例如：Listary、PixPin等
这是因为 start_client_gui.exe 默认以用户权限运行客户端
运行在用户权限的程序无法控制管理员权限的程序

你可以关闭用户权限运行的客户端
尝试使用 start_client_gui_admin.exe
以管理员权限运行客户端




了解更多：Pystand自动UAC提权原理参考

https://github.com/H1DDENADM1N/PyStand/commit/8be144dfa1ef2d145a96b95d8d162498a6f785b0)

"""

with open("history_r.log", "a", encoding="utf-8") as f:
    f.write(f"in start_client_gui_admin.py 1 : id(smart_history_actions_panel.unpinned_groups) = id(start_client_gui.unpinned_groups))\n")
from start_client_gui import start_client_gui
with open("history_r.log", "a", encoding="utf-8") as f:
    f.write(f"in start_client_gui_admin.py 2 : id(til.smart_history_actions_panel.unpinned_groups) = id(util.smart_history_actions_panel.unpinned_groups))\n")

if __name__ == "__main__":
    start_client_gui()