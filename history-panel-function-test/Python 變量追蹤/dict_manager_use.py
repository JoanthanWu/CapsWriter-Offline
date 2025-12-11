# dict_manager_use.py
from multiprocessing import Process
from dict_manager import make_manager, reader, adder, CustomManager
import json
import os
import sys

# 保存Manager连接信息的文件
MANAGER_INFO_FILE = "manager_connection.json"

if __name__ == "__main__":
    # Windows下强制启用spawn模式（避免fork导致的问题）
    from multiprocessing import set_start_method

    try:
        set_start_method('spawn')
    except RuntimeError:
        pass  # 已设置过则忽略

    # 1. 统一authkey
    AUTHKEY = b'my_shared_key_2025'

    # 2. 创建Manager和共享数据
    manager, ns, unpinned_groups = make_manager(authkey=AUTHKEY)
    if manager is None:
        sys.exit(1)

    # 3. 初始化共享数据
    new_group1 = manager.dict({"english": "Hi", "traditional": "嗨"})
    new_group2 = manager.dict({"english": "Hi2", "traditional": "嗨2"})

    # 用Process添加数据（避免主线程直接操作）
    p1 = Process(target=adder, args=(unpinned_groups, new_group1))
    p2 = Process(target=adder, args=(unpinned_groups, new_group2))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    # 4. 打印初始数据
    print("\n=== 初始共享数据 ===")
    reader(unpinned_groups, 2)
    print("完整列表:", [dict(item) for item in unpinned_groups])

    # 5. 保存Manager连接信息（供子脚本读取）
    manager_info = {
        "address": manager.address,
        "authkey": AUTHKEY.decode("latin-1")  # bytes转字符串保存
    }
    with open(MANAGER_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(manager_info, f)

    # 6. 阻塞等待子脚本修改
    print(f"\n=== 等待子脚本修改 ===")
    print(f"Manager地址已保存到: {MANAGER_INFO_FILE}")
    print(f"请运行 dict_manager_use_2.py 后按 Enter 键...")
    input()

    # 7. 打印修改后的结果
    print("\n=== 修改后的共享数据 ===")
    print("完整列表:", [dict(item) for item in unpinned_groups])

    # 8. 清理资源
    if os.path.exists(MANAGER_INFO_FILE):
        os.remove(MANAGER_INFO_FILE)
    manager.shutdown()
    print("\n✅ Manager已关闭，程序结束")