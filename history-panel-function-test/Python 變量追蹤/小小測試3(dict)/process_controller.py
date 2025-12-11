# process_controller.py
from multiprocessing import Process
from modify_process import create_modify_process
from worker_functions import add_key, modify_key


# 非main模块的函数：执行修改进程的创建、启动、等待
def run_modify_process(shared_dict):
    """在非main模块中启动并等待修改进程"""
    # 1. 创建修改进程（传入共享字典）
    p_modify = create_modify_process(shared_dict)
    # 2. 启动进程
    p_modify.start()
    print("【控制模块】修改进程已启动")
    # 3. 等待进程执行完毕
    p_modify.join()
    print("【控制模块】修改进程执行完成")


def create_add_process(shared_dict):
    p_add = Process(target=add_key, args=(shared_dict,))
    p_add.start()
    p_add.join()
    return p_add


