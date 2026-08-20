import my_module

print(my_module.MY_VALUE)

my_module.my_func()

from my_module import my_func

my_func()


from my_module import my_func as f

f()

from itertools import combinations

print(list(combinations([1, 3, 5, 8], 2)))