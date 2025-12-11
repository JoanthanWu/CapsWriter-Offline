from multiprocessing import Manager
import worker_functions

# 复用函数引用（无需修改）
run_add_process = worker_functions.run_add_process
run_modify_process = worker_functions.run_modify_process
run_delete_key_process = worker_functions.run_delete_key_process

if __name__ == "__main__":
    # 1. 创建 Manager 实例（核心：唯一的共享管理器）
    with Manager() as manager:
        shared_list = manager.list()  # 共享列表

        # ========== 步骤1：启动新增进程（传递 manager） ==========
        run_add_process(shared_list, manager)  # 关键：传入 manager
        print(f"【main】shared_list = {[dict(item) for item in shared_list]}")
        print("【main】run_add_process进程执行完成\n")

        # ========== 步骤2：执行修改进程 ==========
        print("【main】开始调用控制模块执行修改进程...")
        run_modify_process(shared_list)
        print(f"【main】shared_list = {[dict(item) for item in shared_list]}")
        print("【main】修改进程已通过控制模块执行完成\n")

        # ========== 步骤3：启动删除进程 ==========
        run_delete_key_process(shared_list)
        print(f"【main】shared_list = {[dict(item) for item in shared_list]}")
        print("【main】run_delete_key_process进程执行完成\n")

        # 验证最终结果
        print("="*50)
        print("【main】最终共享列表：", [dict(item) for item in shared_list])