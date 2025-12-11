from multiprocessing import Process
from worker_functions import add_key

# 创建新增进程
def create_add_process(shared_dict):
    p = Process(target=add_key, args=(shared_dict,))
    return p