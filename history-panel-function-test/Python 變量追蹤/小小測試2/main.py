from multiprocessing import Process, Manager
from add_module import add_key
from modify_module import modify_key
from delete_module import delete_key

if __name__ == "__main__":
    # 1. 主进程创建Manager和共享字典
    with Manager() as manager:
        shared_dict = manager.dict()

        # 2. 启动进程时，将共享字典作为参数传递给各模块的函数
        p1 = Process(target=add_key, args=(shared_dict,))
        p2 = Process(target=modify_key, args=(shared_dict,))
        p3 = Process(target=delete_key, args=(shared_dict,))

        p1.start()
        p2.start()
        p3.start()

        p1.join()
        p2.join()
        p3.join()

        # 3. 主进程读取修改后的共享字典（同步生效）
        print("="*30)
        print("【主模块】最终共享字典：", dict(shared_dict))