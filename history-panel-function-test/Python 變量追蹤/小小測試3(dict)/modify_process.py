from multiprocessing import Process
from worker_functions import modify_key

# 创建修改进程
def create_modify_process(shared_dict):
    p = Process(target=modify_key, args=(shared_dict,))
    return p