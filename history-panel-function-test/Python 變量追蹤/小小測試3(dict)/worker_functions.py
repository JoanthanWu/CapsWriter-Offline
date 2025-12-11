# worker_functions.py
import time
from multiprocessing import Process

# 新增键值
def add_key(shared_dict):
    time.sleep(0.1)
    shared_dict["name"] = "小明"
    shared_dict["lang"] = "繁體中文"
    print(f"【新增进程】共享字典：{dict(shared_dict)}")


def run_add_process(shared_dict):
    p_add = Process(target=add_key, args=(shared_dict,))
    p = Process(target=add_key, args=(shared_dict,))
    p_add.start()
    print("【run_add_process】add进程已启动")
    p_add.join()
    print("【run_add_process】add进程执行完成")


def modify_key(shared_dict):
    time.sleep(0.1)
    while "name" not in shared_dict:
        time.sleep(0.01)
    shared_dict["name"] = "張小明"
    shared_dict["age"] = 25
    print(f"【修改进程】共享字典：{dict(shared_dict)}")


def run_modify_process(shared_dict):
    """在非main模块中启动并等待修改进程"""
    # 1. 创建修改进程（传入共享字典）
    p_modify = Process(target=modify_key, args=(shared_dict,))
    # p_modify = modify_key(shared_dict)
    # 2. 启动进程
    p_modify.start()
    print("【run_modify_process】modify进程已启动")
    # 3. 等待进程执行完毕
    p_modify.join()
    print("【run_modify_process】modify进程执行完成")


# 删除键值
def delete_key(shared_dict):
    time.sleep(0.2)
    if "lang" in shared_dict:
        del shared_dict["lang"]
    print(f"【删除进程】共享字典：{dict(shared_dict)}")


def run_delete_key_process(shared_dict):
    p_delete = Process(target=delete_key, args=(shared_dict,))
    p_delete.start()
    print("【run_delete_key_process】delete进程已启动")
    p_delete.join()
    print("【run_delete_key_process】delete进程执行完成")