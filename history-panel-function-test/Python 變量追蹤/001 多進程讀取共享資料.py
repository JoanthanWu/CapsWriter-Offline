from multiprocessing import Process, Manager
import time
def reader(shared_data, idx):
    print(f"進程讀取到: {shared_data[idx]}")

def writer(shared_data, idx, key, value):
    shared_data[idx][key] = value

if __name__ == "__main__":
    with Manager() as manager:
        test_groups = manager.list([
            {"traditional": "你好"},
            {"simplified": "这是简体", "traditional": "", "english": ""},
            {"traditional": "這是繁體"},
            {"english": "Hello"}
        ])

        # 先修改
        p1 = Process(target=writer, args=(test_groups, 0, "traditional", "修改後的內容"))
        p1.start()
        p1.join()   # 等待修改完成

        # 再讀取
        p2 = Process(target=reader, args=(test_groups, 0))
        p2.start()
        p2.join()
