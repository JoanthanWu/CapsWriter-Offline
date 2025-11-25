# h.py
import sys
import package.a
print(f'==================Now,import package.g==================')
import package.g

h_x = package.a.x

print(f"id(sys.modules['package.a']) = {id(sys.modules['package.a'])}")
print(f'in h: x = {package.a.x}')
print(f'in h: id(a) = {id(package.a)}')
print(f'in h: id(x) = {id(package.a.x)}')

print(f'in h: h_x = {h_x}')
print(f'in h: id(h_x) = {id(h_x)}')

print(f'----------------h.py Done----------------')