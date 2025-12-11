import time

# 修改键值：接收主进程传递的共享字典
def modify_key(shared_dict):
    time.sleep(0.1)
    while "name" not in shared_dict:
        time.sleep(0.01)
    shared_dict["name"] = "張小明"
    shared_dict["age"] = 25
    print(f"【修改模块】共享字典：{dict(shared_dict)}")