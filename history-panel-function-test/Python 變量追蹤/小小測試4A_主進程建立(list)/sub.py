from multiprocessing import Manager
import worker_functions
import main
import keyboard
# 复用函数引用
run_add_process = worker_functions.run_add_process
run_modify_process = worker_functions.run_modify_process
run_delete_key_process = worker_functions.run_delete_key_process

if __name__ == "__main__":

    # ========== 步骤2：执行修改进程 ==========
    print("【sub】开始调用控制模块执行修改进程...")
    run_modify_process(unpinned_groups)
    print(f"【sub】unpinned_groups = {[dict(item) for item in unpinned_groups]}")
    print("【sub】修改进程已通过控制模块执行完成\n")

    # ========== 步骤3：启动删除进程 ==========
    run_delete_key_process(unpinned_groups)
    print(f"【sub】unpinned_groups = {[dict(item) for item in unpinned_groups]}")
    print("【sub】run_delete_key_process进程执行完成\n")

    # 验证最终结果
    print("=" * 50)
    print("【sub】最终共享列表：", [dict(item) for item in unpinned_groups])

    keyboard.wait()