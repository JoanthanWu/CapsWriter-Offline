# 手动维护 ID 到对象的映射（更安全）
obj_map = {}

def register_obj(obj):
    obj_id = id(obj)
    obj_map[obj_id] = obj
    return obj_id

def get_obj(obj_id):
    return obj_map.get(obj_id)

# 测试
my_var = 12345
var_id = register_obj(my_var)
print(get_obj(var_id))  # 12345