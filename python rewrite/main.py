import parser
import itertools


MAX_SKILL_POINTS: int = 595
MAX_STRREQ: int = 320
MAX_DEXREQ: int = 317
MAX_INTREQ: int = 283
MAX_DEFREQ: int = 284
MAX_AGIREQ: int = 333


def get_stat_to_optimise():
    new_input = input('Give stat to optimize: ')
    new_input.strip()
    return new_input


def get_max_best_length():
    new_input = input('Give the max amount of best results to give (lower = faster): ')
    numerical_input = int(new_input.strip().lower())
    return numerical_input


def skill_point_fast_check(stats: dict[str, int]) -> bool:
    str_req = stats.get('strReq', 0)
    dex_req = stats.get('dexReq', 0)
    int_req = stats.get('intReq', 0)
    def_req = stats.get('defReq', 0)
    agi_req = stats.get('agiReq', 0)
    if str_req + dex_req + int_req + def_req + agi_req > MAX_SKILL_POINTS:
        return False
    if str_req > MAX_STRREQ:
        return False
    if dex_req > MAX_DEXREQ:
        return False
    if int_req > MAX_INTREQ:
        return False
    if def_req > MAX_DEFREQ:
        return False
    if agi_req > MAX_AGIREQ:
        return False
    return True



def combine(combo1: dict[str, dict[str, int]], combo2: dict[str, dict[str, int]]):
    combo1_values = list(combo1.values())[0]
    combo2_values = list(combo2.values())[0]
    combo1_keys_set = set(combo1_values.keys())
    combo2_keys_set = set(combo1_values.keys())
    resulting_stats: dict[str, int] = {}
    resulting_name: str = ''.join((list(combo1.keys())[0], ', ', list(combo2.keys())[0]))
    for key in combo1_keys_set.union(combo2_keys_set):
        resulting_stats[key] = combo1_values.get(key, 0) + combo2_values.get(key, 0)
    return {resulting_name: resulting_stats}




def precompute(items1: dict[str,dict[str, int]], items2: dict[str,dict[str, int]]):
    combinations_keys = itertools.product(items1.keys(), items2.keys())
    combinations_values = itertools.product(items1.values(), items2.values())
    for i, key in enumerate(combinations_keys):
        combination = next(combinations_values)
        item1_keys_set = set(combination[0].keys())
        item2_keys_set = set(combination[1].keys())
        resulting_stats: dict[str, int] = {}
        resulting_name: str = ''.join((key[0], ', ', key[1]))
        for key in item1_keys_set.union(item2_keys_set):
            resulting_stats[key] = combination[0].get(key, 0) + combination[1].get(key, 0)
        if not skill_point_fast_check(resulting_stats):
            continue
        yield {resulting_name: resulting_stats}



def dict_from_map_object(to_convert) -> dict[str, dict[str, int]]:
    converted = {}
    for dictionary in to_convert:
        converted.update(dictionary)
    return converted








def get_permutations(database_path):
    stat_to_optimise = get_stat_to_optimise()
    max_best_length = get_max_best_length()
    items = parser.parse_items(database_path)
    helmets, chestplates, leggings, boots, rings, bracelets, necklaces, spears, bows, daggers, wands, reliks = items
    weapons = dict(**spears, **bows, **daggers ,**wands, **reliks)
    
    best_list = []
    worst_best_value = 0

    helmets_chestplates = [x for x in precompute(helmets, chestplates)]
    leggings_boots = [x for x in precompute(leggings, boots)]
    all_rings = [x for x in precompute(rings, rings)]
    bracelets_necklaces = [x for x in precompute(bracelets, necklaces)]

    
    for hccombo in helmets_chestplates:
        for lbcombo in leggings_boots:
            hclbcombo = combine(hccombo, lbcombo)
            if not skill_point_fast_check(list(hclbcombo.values())[0]):
                continue
            for rrcombo in all_rings:
                hclbrrcombo = combine(hclbcombo, rrcombo)
                if not skill_point_fast_check(list(hclbrrcombo.values())[0]):
                    continue
                for bncombo in bracelets_necklaces:
                    hclbrrbncombo = combine(hclbrrcombo, bncombo)
                    final_combo = hclbrrbncombo
                    values = list(final_combo.values())[0]
                    if not skill_point_fast_check(values):
                        continue
                    #TODO: Need to add more fast checks before this one (validitychecks)
                    if values.get(stat_to_optimise, 0) <= worst_best_value:
                        continue
                    #worst_best_value = values.get(stat_to_optimise, 0)
                    best_list.append(final_combo)
                    if len(best_list) > max_best_length:
                        best_list.sort(key= lambda x: x[list(x.keys())[0]][stat_to_optimise])
                        best_list = best_list[1:]
                        worst_best_value = list(best_list[0].values())[0].get(stat_to_optimise, 0)
                    print(best_list)

                    

















def main():
    database_path = "data\\items.json"
    get_permutations(database_path)



if __name__ == "__main__":
    main()
