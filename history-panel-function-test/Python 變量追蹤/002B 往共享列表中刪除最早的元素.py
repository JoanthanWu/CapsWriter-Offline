# main.py
from multiprocessing import Process
from 101_dict_manager import manager, unpinned_groups, reader, adder

if __name__ == "__main__":
    new_group = manager.dict({"english": "Hi", "traditional": "嗨"})

    p_add = Process(target=adder, args=(unpinned_groups, new_group))
    p_add.start()
    p_add.join()

    p_read = Process(target=reader, args=(unpinned_groups, 2))
    p_read.start()
    p_read.join()

    print("完整共享列表:", [dict(item) for item in unpinned_groups])
