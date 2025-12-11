from multiprocessing import Process
from worker_functions import delete_key

# 创建「删除键」的进程
def create_delete_process(shared_dict):
    p = Process(target=delete_key, args=(shared_dict,))
    return p