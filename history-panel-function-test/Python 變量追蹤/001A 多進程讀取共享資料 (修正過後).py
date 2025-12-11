from multiprocessing import Process, Manager

def reader(shared_data, idx):
    print(f"進程讀取到: {shared_data[idx]}")

def writer(shared_data, idx, key, value):
    shared_data[idx][key] = value  # 此时修改的是共享字典的键值对

if __name__ == "__main__":
    with Manager() as manager:
        # 关键：用 manager.dict() 替代普通字典
        test_groups = manager.list([
            manager.dict({"traditional": "你好"}),
            manager.dict({"simplified": "这是简体", "traditional": "", "english": ""}),
            manager.dict({"traditional": "這是繁體"}),
            manager.dict({"english": "Hello"})
        ])

        # 先修改
        p1 = Process(target=writer, args=(test_groups, 0, "traditional", "修改後的內容"))
        p2 = Process(target=reader, args=(test_groups, 0))

        p1.start()
        p1.join()

        # 再讀取

        p2.start()
        p2.join()