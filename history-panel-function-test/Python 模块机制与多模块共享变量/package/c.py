# c.py
import a
import b
import sys

#
a.x += 1

print(f'in c: x = {a.x}')
print(f'in c: id(a) = {id(a)}')
print(f"id(sys.modules['a']) = {id(sys.modules['a'])}")