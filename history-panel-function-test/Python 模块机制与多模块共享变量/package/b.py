# b.py
import a
print(f'in b start: x = {a.x}')
print(f'in b start: id(x) = {id(a.x)}')
print(f'in b start: y = {a.y}')
print(f'in b start: id(y) = {id(a.y)}')
a.x += 1
a.y[0] = 0
print(f'in b: x = {a.x}')
print(f'in b: id(a) = {id(a)}')
print(f'in b: id(x) = {id(a.x)}')
print(f'in b: y = {a.y}')
print(f'in b: id(y) = {id(a.y)}')
print(f'----------------b.py Done----------------')