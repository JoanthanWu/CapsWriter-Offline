# d.py
from a import x, y
print(f'in d: x = {x}')
print(f'in d: id(x) = {id(x)}')
print(f'in d: y = {y}')
print(f'in d: id(y) = {id(y)}')

print(f'==================Now,import b==================')
import b
print(f'in d: x = {x}')
print(f'in d: id(x) = {id(x)}')
print(f'in d: y = {y}')
print(f'in d: id(y) = {id(y)}')

print(f'==================Now,from a import x, y==================')
from a import x, y
print(f'in d: x = {x}')
print(f'in d: id(x) = {id(x)}')
print(f'in d: y = {y}')
print(f'in d: id(y) = {id(y)}')

print(f'----------------d.py Done----------------')

'''
from a import x, y
# 全稱是:
x, y = sys.modules['a'].x, sys.modules['a'].y


#  再次 `from a import x, y` 后 x,y 都更新为 a.x,a.y，所以如果是 from import var 需要手动刷新，对需要修改的共享变量不建议使用 from import var
from a import x, y
x,y = a.x,a.y
'''