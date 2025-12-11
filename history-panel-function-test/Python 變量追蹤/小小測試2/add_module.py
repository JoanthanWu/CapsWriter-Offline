import time

# 新增键值：接收主进程传递的共享字典
def add_key(shared_dict):
    time.sleep(0.1)
    shared_dict["name"] = "小明"
    shared_dict["lang"] = "繁體中文"
    print(f"【新增模块】共享字典：{dict(shared_dict)}")