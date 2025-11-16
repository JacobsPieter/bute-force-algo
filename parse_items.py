import json
def _get_data(file_path):
    with open(file_path, 'rb') as file:
        file.seek(1682485)
        problematic_bytes = file.read(50)
        print(f"Bytes at position 1682485: {problematic_bytes}")

def get_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data


def get_items_and_sets():
    data = get_data('items.json')
    items = data['items']
    sets = data['sets']
    return items, sets


def get_data_keys(item: dict) -> dict:
    item_data = {}
    for key in item.keys():
        if isinstance(item[key], (float)):
            item_data[key] = item[key]
        elif isinstance(item[key], (int)):
            item_data[key] = float(item[key])
    return item_data




def parse_items():
    items, sets = get_items_and_sets()
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
    return helmets, chestplates, leggings, boots, rings, bracelets, necklaces, spears, bows, daggers, wands, reliks


def make_lists_from_dicts(input_dict: dict) -> tuple[list, list]:
    keys, values = [], []
    keys = list(input_dict.keys())
    values = list(input_dict.values())
    return (keys, values)
    



if __name__ == "__main__":
    print(parse_items())