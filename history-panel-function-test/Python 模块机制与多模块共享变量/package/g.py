# g.py
from . import a
#❌ import a

a.x += 1
print(f'in g: x = {a.x}')
print(f'in g: id(a) = {id(a)}')

print(f'----------------g.py Done----------------')