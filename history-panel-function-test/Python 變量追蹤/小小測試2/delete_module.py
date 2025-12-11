import time

# 删除键值：接收主进程传递的共享字典
def delete_key(shared_dict):
    time.sleep(0.2)
    if "lang" in shared_dict:
        del shared_dict["lang"]
    print(f"【删除模块】共享字典：{dict(shared_dict)}")