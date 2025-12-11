# dict_manager.py
def reader(shared_data, idx):
    print(f"讀取索引 {idx} 的數據: {shared_data[idx]}")

def adder(shared_data, new_data):
    shared_data.append(new_data)
