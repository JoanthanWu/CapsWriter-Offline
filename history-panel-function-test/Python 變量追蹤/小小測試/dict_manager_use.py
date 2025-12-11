# dict_manager_use.py
from multiprocessing import Process, Manager
from dict_manager import reader, adder

if __name__ == "__main__":
    with Manager() as manager:
        unpinned_groups = manager.list([
            manager.dict({"traditional": ""}),
            manager.dict({"simplified": ""}),
        ])

        new_group = manager.dict({"english": "Hi", "traditional": "嗨"})
        new_group2 = manager.dict({"english": "Hi2", "traditional": "嗨2"})

        p_add = Process(target=adder, args=(unpinned_groups, new_group))
        p_add.start(); p_add.join()

        p_add2 = Process(target=adder, args=(unpinned_groups, new_group2))
        p_add2.start(); p_add2.join()

        p_read = Process(target=reader, args=(unpinned_groups, 2))
        p_read.start(); p_read.join()

        print("完整共享列表:", [dict(item) for item in unpinned_groups])
