# main.py
from multiprocessing import Manager
import worker_functions
run_add_process = worker_functions.run_add_process
run_modify_process = worker_functions.run_modify_process
run_delete_key_process = worker_functions.run_delete_key_process

if __name__ == "__main__":
    # 1. 主进程创建唯一的共享字典（核心：所有进程的共享源）
    with Manager() as manager:
        shared_dict = manager.dict()

        # ========== 步骤1：main中启动新增进程 ==========
        p_add = run_add_process(shared_dict)
        print(f"【main】shared_dict = {shared_dict}")
        print("【main】run_add_process进程执行完成\n")

        # ========== 步骤2：调用非main模块执行修改进程 ==========
        print("【main】开始调用控制模块执行修改进程...")
        run_modify_process(shared_dict)  # 关键：把共享字典传给控制模块
        print(f"【main】shared_dict = {shared_dict}")
        print("【main】修改进程已通过控制模块执行完成\n")

        # ========== 步骤3：main中启动删除进程 ==========
        p_delete = run_delete_key_process(shared_dict)
        print(f"【main】shared_dict = {shared_dict}")
        print("【main】run_delete_key_process进程执行完成\n")

        # 验证最终结果
        print("="*50)
        print("【main】最终共享字典：", dict(shared_dict))