import sort
import filtering
import parse_items
import numpy as np
from numba import njit
import json


#test data for different item types


def get_stat_to_optimize() -> str:
    stat = input('Enter the stat to optimize: ').strip().lower()
    return stat

def get_required_stats() -> list[str]:
    stats_input = input('Enter the required stats (comma-separated): ').strip().lower()
    required_stats = [stat.strip() for stat in stats_input.split(',')]
    return required_stats

def get_min_value_for_stat(required_stats: list[str]) -> list[int]:
    min_value_input = input('Enter the minimum value for the required stats (comma-seperated, same order as required stats): ').strip()
    min_values = [int(value.strip()) for value in min_value_input.split(',')]
    return min_values

def get_required_stats_dict(stat_to_optimise: str) -> dict[str, int]:
    required_stats = get_required_stats()
    required_stats_dict: dict[str, int] = {}
    if required_stats != ['']:
        min_values = get_min_value_for_stat(required_stats)
        for i, stat in enumerate(required_stats):
            if stat == stat_to_optimise:
                continue
            required_stats_dict[stat] = min_values[i]
    required_stats_dict[stat_to_optimise] = -1
    return required_stats_dict


def combine_stats(item_1: dict, item_2: dict) -> dict:
    combined: dict = {}
    for stat in set(item_1.keys()).union(item_2.keys()):
        if item_1.get(stat) is None:
            combined[stat] = item_2.get(stat, 0)
            continue
        if item_2.get(stat) is None:
            combined[stat] = item_1.get(stat, 0)
            continue
        if isinstance(item_1[stat], int | float) and isinstance(item_2[stat], int | float):
            combined[stat] = item_1.get(stat, 0) + item_2.get(stat, 0)
        elif isinstance(item_1[stat], str) and isinstance(item_2[stat], str):
            combined[stat] = item_1.get(stat, '') + ', ' + item_2.get(stat, '')
        elif isinstance(item_1[stat], list) and isinstance(item_2[stat], list):
            combined[stat] = item_1.get(stat, []) + item_2.get(stat, [])
        else:
            print(f'Unknown stat type for stat {stat}')
    return combined


def get_stats_for_item_groups(items_type_1: dict, items_type_2: dict) -> dict:
    combinations: dict = {}
    for item_type_1 in items_type_1.keys():
        for item_type_2 in items_type_2.keys():
            combination: dict = combine_stats(items_type_1[item_type_1], items_type_2[item_type_2])
            combinations[f'{item_type_1} + {item_type_2}'] = combination
    return combinations



def load_combinations_from_file(file_name: str, parts: int, part_of_group: int):
    with open(file_name, 'r') as file:
        combinations = json.load(file)
    combinations_keys = list(combinations.keys())
    combinations_values = list(combinations.values())
    length_combinations = len(combinations_keys)
    length_combinations_group = length_combinations//parts
    selection_first = part_of_group * length_combinations_group
    selection_last = part_of_group * length_combinations_group + length_combinations_group
    part_of_combinations  = {}.fromkeys(combinations_keys[selection_first:selection_last], (value for value in combinations_values[selection_first: selection_last]))
    return part_of_combinations








def get_all_combinations() -> dict[str, dict[str, int]]:
    items = parse_items.parse_items()
    print('Generating all possible combinations of items...')
    print('This may take a while depending on the number of items...')
    print('starting the top parts of the armour...')
    top_parts = get_stats_for_item_groups(items[0], items[1])
    with open("top_parts.json", "w") as outfile:
        json.dump(top_parts, outfile, indent=4)
    top_parts = {}
    print('now the bottom parts of the armour...')
    bottom_parts = get_stats_for_item_groups(items[2], items[3])
    with open("bottom_parts.json", "w") as outfile:
        json.dump(bottom_parts, outfile, indent=4)
    bottom_parts = {}
    print('now the jewelry...')
    print('first the rings...')
    rings_combinations = get_stats_for_item_groups(items[4], items[5])
    with open("ring_combinations.json", "w") as outfile:
        json.dump(rings_combinations, outfile, indent=4)
    rings_combinations = {}
    print('then the big jewelry (bracelets and necklaces)...')
    big_jewelry = get_stats_for_item_groups(items[6], items[7])
    with open("big_jewelry.json", "w") as outfile:
        json.dump(big_jewelry, outfile, indent=4)
    big_jewelry = {}
    print('combining rings with big jewels...')
    rings_combinations1 = load_combinations_from_file('ring_combinations.json', 4, 0)
    big_jewelry1 = load_combinations_from_file('big_jewelry.json', 4, 0)
    jewelry_combinations1 = get_stats_for_item_groups(rings_combinations1, big_jewelry1)
    with open("jewelry_combinations1.json", 'w') as outfile:
        json.dump(jewelry_combinations1, outfile, indent=4)
    print('finished first run')
    """     rings_combinations2  = {}
    rings_combinations_keys = list(rings_combinations.keys())
    for i in range(len(rings_combinations_keys)//2):
        rings_combinations2[rings_combinations_keys[i]] = rings_combinations[rings_combinations_keys[i]]
    jewelry_combinations2 = get_stats_for_item_groups(rings_combinations2, big_jewelry)
    jewelry_combinations = jewelry_combinations1
    jewelry_combinations.update(jewelry_combinations2)"""
    print('combining armour parts...')
    protections = get_stats_for_item_groups(top_parts, bottom_parts)
    print('now the total of armour and jewelry...')
    equipment_combinations = get_stats_for_item_groups(protections, jewelry_combinations1)
    print('finally adding the weapons...')
    weapons = {}
    for weapon_group in items[8:12]:
        weapons.update(weapon_group)
    all_combinations = get_stats_for_item_groups(weapons, equipment_combinations)
    print('All combinations generated.')
    return all_combinations



def sort_combinations_by_stat(combinations: dict[str, dict[str, int]], stat: str) -> list[str]:
    stat_values: dict[str, int] = {}
    for combo_name, stats in combinations.items():
        stat_values[combo_name] = stats.get(stat, 0)
    sorted_combinations = sort.sort_dict(stat_values)
    return sorted_combinations[0]


def return_comibinations(filtered_combinations: dict[str, dict[str, int]], stat_to_optimize: str):
    if len(filtered_combinations) == 0:
        print('No combinations found that meet the required stats.')
        return
    if len(filtered_combinations) == 1:
        print('Only one combination found that meets the required stats:')
        for name, stats in filtered_combinations.items():
            print(f'{name}: {stats}')
        return
    print(f'Found {len(filtered_combinations)} combinations that meet the required stats. Sorting by {stat_to_optimize}...')
    print('this may take a while...')
    sorted_names = sort_combinations_by_stat(filtered_combinations, stat_to_optimize)
    for name in sorted_names:
        stats = filtered_combinations[name]
        print(f'{name}: {stats}')





def main():
    stat_to_optimize = get_stat_to_optimize()
    required_stats = get_required_stats_dict(stat_to_optimize)
    all_combinations = get_all_combinations()
    filtered_combinations = filtering.filter(all_combinations, required_stats)
    return_comibinations(filtered_combinations, stat_to_optimize)



if __name__ == '__main__':
    main()