# d.py
from a import x, y
print(f'in d: x = {x}')
print(f'in d: id(x) = {id(x)}')

print(f'==================Now,import b==================')
import b
print(f'in d: x = {x}')
print(f'in d: y = {y}')
print(f'in d: id(x) = {id(x)}')

print(f'==================Now,from a import x, y==================')
from a import x, y
print(f'in d: x = {x}')
print(f'in d: id(x) = {id(x)}')

print(f'----------------d.py Done----------------')