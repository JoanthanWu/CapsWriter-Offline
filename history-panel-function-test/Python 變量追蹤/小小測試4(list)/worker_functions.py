import time
from multiprocessing import Process

# ========== 新增：接收 manager 参数，创建共享字典 ==========
def add_key(shared_list, manager):  # 新增 manager 参数
    time.sleep(0.1)
    # 用 main 传递的 manager 创建共享字典（关键：避免依赖私有属性）
    user_dict = manager.dict({
        "name": "小明",
        "lang": "繁體中文"
    })
    shared_list.append(user_dict)
    print(f"【新增进程】共享列表：{[dict(item) for item in shared_list]}")


def run_add_process(shared_list, manager):  # 新增 manager 参数
    # 把 manager 传递给业务函数
    p_add = Process(target=add_key, args=(shared_list, manager))
    p_add.start()
    print("【run_add_process】add进程已启动")
    p_add.join()
    print("【run_add_process】add进程执行完成")


# ========== 修改：无需新增参数（仅操作已有共享字典） ==========
def modify_key(shared_list):
    time.sleep(0.1)
    while len(shared_list) == 0:
        time.sleep(0.01)
    shared_list[0]["name"] = "張小明"
    shared_list[0]["age"] = 25
    print(f"【修改进程】共享列表：{[dict(item) for item in shared_list]}")


def run_modify_process(shared_list):
    p_modify = Process(target=modify_key, args=(shared_list,))
    p_modify.start()
    print("【run_modify_process】modify进程已启动")
    p_modify.join()
    print("【run_modify_process】modify进程执行完成")


# ========== 删除：无需新增参数 ==========
def delete_key(shared_list):
    time.sleep(0.2)
    if len(shared_list) > 0 and "lang" in shared_list[0]:
        del shared_list[0]["lang"]
    print(f"【删除进程】共享列表：{[dict(item) for item in shared_list]}")


def run_delete_key_process(shared_list):
    p_delete = Process(target=delete_key, args=(shared_list,))
    p_delete.start()
    print("【run_delete_key_process】delete进程已启动")
    p_delete.join()
    print("【run_delete_key_process】delete进程执行完成")