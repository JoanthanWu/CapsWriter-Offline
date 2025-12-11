import time
from multiprocessing import Process

# ========== 新增：接收提前创建的共享字典，追加到列表 ==========
def add_key(unpinned_groups, pre_created_dict):  # 接收main创建的共享字典
    time.sleep(0.1)
    unpinned_groups.append(pre_created_dict)  # 直接追加已创建的共享字典
    print(f"【新增进程】共享列表：{[dict(item) for item in unpinned_groups]}")


def run_add_process(unpinned_groups, pre_created_dict):  # 接收共享字典参数
    # 仅传递共享列表和提前创建的共享字典（无manager）
    p_add = Process(target=add_key, args=(unpinned_groups, pre_created_dict))
    p_add.start()
    print("【run_add_process】add进程已启动")
    p_add.join()
    print("【run_add_process】add进程执行完成")


# ========== 修改/删除逻辑：完全不变 ==========
def modify_key(unpinned_groups):
    time.sleep(0.1)
    while len(unpinned_groups) == 0:
        time.sleep(0.01)
    unpinned_groups[0]["name"] = "張小明"
    unpinned_groups[0]["age"] = 25
    print(f"【修改进程】共享列表：{[dict(item) for item in unpinned_groups]}")


def run_modify_process(unpinned_groups):
    p_modify = Process(target=modify_key, args=(unpinned_groups,))
    p_modify.start()
    print("【run_modify_process】modify进程已启动")
    p_modify.join()
    print("【run_modify_process】modify进程执行完成")


def delete_key(unpinned_groups):
    time.sleep(0.2)
    if len(unpinned_groups) > 0 and "lang" in unpinned_groups[0]:
        del unpinned_groups[0]["lang"]
    print(f"【删除进程】共享列表：{[dict(item) for item in unpinned_groups]}")


def run_delete_key_process(unpinned_groups):
    p_delete = Process(target=delete_key, args=(unpinned_groups,))
    p_delete.start()
    print("【run_delete_key_process】delete进程已启动")
    p_delete.join()
    print("【run_delete_key_process】delete进程执行完成")