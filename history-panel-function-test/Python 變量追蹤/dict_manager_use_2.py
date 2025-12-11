# dict_manager_use_2.py
from multiprocessing import managers
import json
import sys
from dict_manager import CustomManager  # 导入全局的CustomManager

# 连接信息文件
MANAGER_INFO_FILE = "manager_connection.json"


def connect_to_remote_manager():
    """连接到主进程的Manager服务器"""
    # 1. 读取连接信息
    try:
        with open(MANAGER_INFO_FILE, "r", encoding="utf-8") as f:
            info = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误：未找到 {MANAGER_INFO_FILE}，请先运行 dict_manager_use.py")
        sys.exit(1)

    # 2. 还原地址和authkey
    manager_addr = tuple(info["address"])
    authkey = info["authkey"].encode("latin-1")

    # 3. 使用全局CustomManager连接（无需重新注册，已全局注册）
    try:
        manager = CustomManager(address=manager_addr, authkey=authkey)
        manager.connect()  # 建立连接
        print(f"✅ 成功连接到Manager服务器: {manager_addr}")
        return manager
    except Exception as e:
        print(f"❌ 连接失败: {e}", file=sys.stderr)
        print("提示：请确保主进程的Manager仍在运行，且authkey一致")
        sys.exit(1)


if __name__ == "__main__":
    # 1. 连接到主进程的Manager
    manager = connect_to_remote_manager()

    # 2. 获取共享的Namespace和unpinned_groups
    ns = manager.Namespace()
    unpinned_groups = ns.unpinned_groups

    # 3. 打印当前数据
    print("\n=== 连接成功，当前共享数据 ===")
    print("列表长度:", len(unpinned_groups))
    print("完整列表:", [dict(item) for item in unpinned_groups])

    # 4. 修改共享字典（核心操作）
    print("\n=== 开始修改共享字典 ===")

    # 示例1：修改索引2的字典
    if len(unpinned_groups) > 2:
        target_dict = unpinned_groups[2]
        print(f"\n修改前（索引2）: {dict(target_dict)}")
        target_dict["traditional"] = "嗨_修改后"
        target_dict["japanese"] = "こんにちは"
        print(f"修改后（索引2）: {dict(target_dict)}")

    # 示例2：修改索引3的字典
    if len(unpinned_groups) > 3:
        target_dict2 = unpinned_groups[3]
        print(f"\n修改前（索引3）: {dict(target_dict2)}")
        target_dict2["traditional"] = "嗨2_修改后"
        target_dict2["korean"] = "안녕하세요"
        print(f"修改后（索引3）: {dict(target_dict2)}")

    # 示例3：添加新字典
    new_dict = manager.dict({
        "english": "Hello",
        "traditional": "你好",
        "simplified": "你好"
    })
    unpinned_groups.append(new_dict)
    print(f"\n✅ 添加新字典（索引{len(unpinned_groups) - 1}）: {dict(new_dict)}")

    # 5. 打印最终结果
    print("\n=== 子脚本修改完成 ===")
    print("最终共享列表:", [dict(item) for item in unpinned_groups])
    print("\n请回到 dict_manager_use.py 按 Enter 查看结果！")