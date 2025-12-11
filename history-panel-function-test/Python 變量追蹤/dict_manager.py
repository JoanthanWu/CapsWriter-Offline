# dict_manager.py
from multiprocessing import managers, Process
import sys

# ========== 核心修正：CustomManager 移到全局作用域 ==========
class CustomManager(managers.BaseManager):
    """全局自定义Manager类（解决pickle序列化问题）"""
    pass

# 注册需要共享的类型（全局注册，主/子进程都能识别）
CustomManager.register('list', managers.ListProxy)
CustomManager.register('dict', managers.DictProxy)
CustomManager.register('Namespace', managers.NamespaceProxy)

def make_manager(authkey=b'my_shared_key_2025'):
    """创建Manager并初始化共享数据（全局类，可pickle）"""
    try:
        # 创建Manager实例（设置authkey）
        manager = CustomManager(authkey=authkey)
        # Windows下必须用start()启动Manager进程（Linux/macOS同理）
        manager.start()
        print(f"✅ Manager启动成功，地址: {manager.address}")
    except Exception as e:
        print(f"❌ Manager创建失败: {e}", file=sys.stderr)
        return None, None, None

    # 初始化共享数据
    ns = manager.Namespace()  # 命名空间（存储共享对象引用）
    # 共享列表（内部是manager.dict）
    unpinned_groups = manager.list([
        manager.dict({"traditional": ""}),
        manager.dict({"simplified": ""}),
    ])
    ns.unpinned_groups = unpinned_groups  # 绑定到命名空间

    return manager, ns, unpinned_groups

# 辅助函数：读取指定索引的字典
def reader(shared_data, idx):
    if idx < len(shared_data):
        print(f"讀取索引 {idx} 的數據: {dict(shared_data[idx])}")
    else:
        print(f"索引 {idx} 不存在，列表长度: {len(shared_data)}")

# 辅助函数：添加新字典到共享列表
def adder(shared_data, new_data):
    shared_data.append(new_data)
    print(f"添加新数据后列表长度: {len(shared_data)}")