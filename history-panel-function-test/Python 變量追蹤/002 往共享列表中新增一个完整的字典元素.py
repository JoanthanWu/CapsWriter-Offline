from multiprocessing import Process, Manager


# 读取指定位置数据（验证新增结果）
def reader(shared_data, idx):
    print(f"讀取索引 {idx} 的數據: {shared_data[idx]}")


# 新增一组数据到共享列表（append 追加/insert 插入）
def adder(shared_data, new_data):
    # 方式1：追加到列表末尾（最常用）
    shared_data.append(new_data)
    # 方式2：插入到指定位置（比如索引1）
    # shared_data.insert(1, new_data)


if __name__ == "__main__":
    with Manager() as manager:
        # 初始化共享列表（内部字典均为 manager.dict）
        test_groups = manager.list([
            manager.dict({"traditional": "你好"}),
            manager.dict({"simplified": "这是简体"}),
        ])

        # 待新增的一组数据（必须用 manager.dict 创建）
        new_group = manager.dict({"english": "Hi", "traditional": "嗨"})

        # 启动子进程执行「新增数据」操作
        p_add = Process(target=adder, args=(test_groups, new_group))
        p_add.start()
        p_add.join()  # 等待新增完成

        # 读取验证：新增的数据在列表末尾（索引2）
        p_read = Process(target=reader, args=(test_groups, 2))
        p_read.start()
        p_read.join()

        # 可选：打印完整列表，验证所有数据
        print("完整共享列表:", list(test_groups))