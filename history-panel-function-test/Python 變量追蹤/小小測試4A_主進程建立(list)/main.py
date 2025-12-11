from multiprocessing import Manager
import worker_functions
import keyboard
# 复用函数引用
run_add_process = worker_functions.run_add_process
run_modify_process = worker_functions.run_modify_process
run_delete_key_process = worker_functions.run_delete_key_process

if __name__ == "__main__":
    # 1. 创建 Manager 实例和共享列表（核心）
    with Manager() as manager:
        unpinned_groups = manager.list()  # 共享列表

        # 关键：在 main 进程提前创建共享字典（避免子进程传递 manager）
        pre_created_dict = manager.dict({
            "name": "小明",
            "lang": "繁體中文"
        })

        # ========== 步骤1：启动新增进程（传递共享列表+提前创建的字典） ==========
        run_add_process(unpinned_groups, pre_created_dict)  # 无manager参数
        print(f"【main】unpinned_groups = {[dict(item) for item in unpinned_groups]}")
        print("【main】run_add_process进程执行完成\n")

        # ========== 步骤2：执行修改进程 ==========
        print("【main】开始调用控制模块执行修改进程...")
        run_modify_process(unpinned_groups)
        print(f"【main】unpinned_groups = {[dict(item) for item in unpinned_groups]}")
        print("【main】修改进程已通过控制模块执行完成\n")

        # ========== 步骤3：启动删除进程 ==========
        run_delete_key_process(unpinned_groups)
        print(f"【main】unpinned_groups = {[dict(item) for item in unpinned_groups]}")
        print("【main】run_delete_key_process进程执行完成\n")

        # 验证最终结果
        print("=" * 50)
        print("【main】最终共享列表：", [dict(item) for item in unpinned_groups])

        keyboard.wait()