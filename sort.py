import numpy as np
from numba import njit

class Counter(int):
    def __init__(self):
        self.count: int = 0

    def increment(self):
        self.count += 1
    
    def set(self, value: int):
        self.count = value

    def get(self):
        return self.count


@njit
def bubbleSort(str_arr: list[str], int_arr: list[int]) -> tuple[list[str], list[int]]:
    n = len(str_arr)
    for i in range(n):
        swapped = False
        for j in range(0, n-i-1):
            if int_arr[j] > int_arr[j+1]:
                int_arr[j], int_arr[j+1] = int_arr[j+1], int_arr[j]
                str_arr[j], str_arr[j+1] = str_arr[j+1], str_arr[j]
                swapped = True
        if swapped == False:
            break
    return str_arr, int_arr


def sort_dict(unsorted_dict: dict[str, int]) -> tuple[list[str], list[int]]:
    counter = Counter()
    keys_list = list(unsorted_dict.keys())
    values_list = list(unsorted_dict.values())
    sorted_keys, sorted_values = bubbleSort(keys_list, values_list)
    return (sorted_keys, sorted_values)


dictionary = {'a': 5, 'b': 3, 'c': 8, 'd': 1}
sorted_keys, sorted_values = sort_dict(dictionary)
print("Sorted Keys:", sorted_keys)
print("Sorted Values:", sorted_values)

