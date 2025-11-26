import human_readable_stat_names_and_indices

import json
import numpy as np




def _get_data(file_path):
    with open(file_path, 'rb') as file:
        file.seek(1682485)
        problematic_bytes = file.read(50)
        print(f"Bytes at position 1682485: {problematic_bytes}")

def get_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


def get_items_and_sets(data_file):
    data = get_data(data_file)
    items = data['items']
    sets = data['sets']
    return items, sets


def get_data_keys(item: dict) -> dict:
    valid_keys = [key for key in item.keys() if isinstance(item[key], (int, float))]
    return dict(zip(valid_keys, [int(item[key]) for key in valid_keys]))




def parse_items(data_file):
    items, sets = get_items_and_sets(data_file)
    helmets = {}
    chestplates = {}
    leggings = {}
    boots = {}
    rings = {}
    bracelets = {}
    necklaces = {}
    spears = {}
    bows = {}
    daggers = {}
    wands = {}
    reliks = {}
    for item in items:
        match item['type']:
            case 'helmet':
                helmets[item['name']] = get_data_keys(item)
            case 'chestplate':
                chestplates[item['name']] = get_data_keys(item)
            case 'leggings':
                leggings[item['name']] = get_data_keys(item)
            case 'boots':
                boots[item['name']] = get_data_keys(item)
            case 'ring':
                rings[item['name']] = get_data_keys(item)
            case 'bracelet':
                bracelets[item['name']] = get_data_keys(item)
            case 'necklace':
                necklaces[item['name']] = get_data_keys(item)
            case 'spear':
                spears[item['name']] = get_data_keys(item)
            case 'bow':
                bows[item['name']] = get_data_keys(item)
            case 'dagger':
                daggers[item['name']] = get_data_keys(item)
            case 'wand':
                wands[item['name']] = get_data_keys(item)
            case 'relik':
                reliks[item['name']] = get_data_keys(item)
            case _:
                print(f"Unknown item type: {item['type']}")
    

    keys_generator = map(make_numpy_arrays_stat_keys, [helmets, chestplates, leggings, boots, rings, bracelets, necklaces, spears, bows, daggers, wands, reliks])
    all_stat_keys = set()
    for keys in keys_generator:
        all_stat_keys |= keys
    ordered_stats = sorted(all_stat_keys)
    
    new_helmets = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in helmets.items()]
    new_chestplates = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in chestplates.items()]
    new_leggings = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in leggings.items()]
    new_boots = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in boots.items()]
    new_rings = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in rings.items()]
    new_bracelets = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in bracelets.items()]
    new_necklaces = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in necklaces.items()]
    new_spears = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in spears.items()]
    new_bows = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in bows.items()]
    new_daggers = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in daggers.items()]
    new_wands = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in wands.items()]
    new_reliks = [(name, np.array([values.get(stat_key, 0) for stat_key in ordered_stats])) for name, values in reliks.items()]
    
    return new_helmets, new_chestplates, new_leggings, new_boots, new_rings, new_bracelets, new_necklaces, new_spears, new_bows, new_daggers, new_wands, new_reliks


def make_numpy_arrays_stat_keys(category: dict[str, dict[str, int]]):
    all_keys = set()
    for stats in category.values():
        all_keys |= set(stats.keys())
    return all_keys
    



if __name__ == "__main__":
    parse_items("data\\items.json")