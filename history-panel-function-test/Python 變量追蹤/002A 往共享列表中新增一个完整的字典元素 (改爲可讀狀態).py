from multiprocessing import Process, Manager


def reader(shared_data, idx):
    print(f"讀取索引 {idx} 的數據: {shared_data[idx]}")


def adder(shared_data, new_data):
    shared_data.append(new_data)


if __name__ == "__main__":
    with Manager() as manager:
        test_groups = manager.list([
            manager.dict({"traditional": "你好"}),
            manager.dict({"simplified": "这是简体"}),
        ])
        new_group = manager.dict({"english": "Hi", "traditional": "嗨"})

        p_add = Process(target=adder, args=(test_groups, new_group))
        p_add.start()
        p_add.join()

        p_read = Process(target=reader, args=(test_groups, 2))
        p_read.start()
        p_read.join()

        # 关键：遍历列表，将每个 DictProxy 转为普通字典
        print("完整共享列表:", [dict(item) for item in test_groups])
        print("完整共享列表 ID :", id([dict(item) for item in test_groups]))
        print("完整共享列表 ID :", id(test_groups))