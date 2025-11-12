helmets = {
    'Iron Helmet': {'defense': 5, 'weight': 10},
    'Steel Helmet': {'defense': 8, 'weight': 12},
    'Golden Helmet': {'defense': 6, 'weight': 9},
    'Diamond Helmet': {'defense': 12, 'weight': 15},
}
armors = {
    'Leather Armor': {'defense': 15, 'weight': 25},
    'Chainmail Armor': {'defense': 25, 'weight': 40},
    'Plate Armor': {'defense': 40, 'weight': 60},
}
leggings = {
    'Cloth Leggings': {'defense': 3, 'weight': 5},
    'Leather Leggings': {'defense': 7, 'weight': 15},
    'Iron Leggings': {'defense': 12, 'weight': 30},
}
boots = {
    'Cloth Boots': {'defense': 2, 'weight': 4},
    'Leather Boots': {'defense': 5, 'weight': 10},
    'Iron Boots': {'defense': 10, 'weight': 20},
}
rings = {
    'Silver Ring': {'magic': 5, 'weight': 1},
    'Gold Ring': {'magic': 10, 'weight': 2},
    'Platinum Ring': {'magic': 15, 'weight': 3},
}
bracelets = {
    'Silver Bracelet': {'magic': 3, 'weight': 1},
    'Gold Bracelet': {'magic': 7, 'weight': 2},
    'Platinum Bracelet': {'magic': 12, 'weight': 3},
}
necklaces = {
    'Silver Necklace': {'magic': 4, 'weight': 1},
    'Gold Necklace': {'magic': 9, 'weight': 2},
    'Platinum Necklace': {'magic': 14, 'weight': 3},
}






def combine_stats(item_1: dict[str, int], item_2: dict[str, int]) -> dict[str, int]:
    combined: dict[str, int] = {}
    for stat in set(item_1.keys()).union(item_2.keys()):
        combined[stat] = item_1.get(stat, 0) + item_2.get(stat, 0)
    return combined


def get_stats_for_item_groups(items_type_1: dict[str, dict[str, int]], items_type_2: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    combinations: dict[str, dict[str, int]] = {}
    for item_type_1 in items_type_1:
        for item_type_2 in items_type_2:
            combination: dict[str, int] = combine_stats(items_type_1[item_type_1], items_type_2[item_type_2])
            combinations[f'{item_type_1} + {item_type_2}'] = combination
    return combinations

if __name__ == '__main__':
    top_parts = get_stats_for_item_groups(helmets, armors)
    bottom_parts = get_stats_for_item_groups(leggings, boots)
    rings_combinations = get_stats_for_item_groups(rings, rings)
    big_jewels = get_stats_for_item_groups(bracelets, necklaces)
    jewelry_combinations = get_stats_for_item_groups(rings_combinations, big_jewels)
    protections = get_stats_for_item_groups(top_parts, bottom_parts)
    all_combinations = get_stats_for_item_groups(protections, jewelry_combinations)
    for combo_name, stats in all_combinations.items():
        print(f'{combo_name}: {stats}')