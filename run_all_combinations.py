import parse_items
import sort
import numba.typed
from numba import njit


MAX_SKILL_POINTS = 100 + 390

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

def get_required_stats_dict(stat_to_optimise: str) -> dict:
    required_stats = get_required_stats()
    required_stats_dict: dict = {}
    if required_stats != ['']:
        min_values = get_min_value_for_stat(required_stats)
        for i, stat in enumerate(required_stats):
            if stat == stat_to_optimise:
                continue
            required_stats_dict[stat] = min_values[i]
    required_stats_dict[stat_to_optimise] = None
    return required_stats_dict


def combine_stats(item1_stats: tuple[list[str], list[int]], item2_stats: tuple[list[str], list[int]]) -> tuple[list[str], list[int]]:
    combined_stats: tuple[list[str], list[int]] = (['' for i in range(len(item1_stats[0])+len(item2_stats[0]))], [0 for i in range(len(item1_stats[1])+len(item2_stats[1]))])
    index = 0
    for i in range(len(item1_stats[0])):
        combined_stats[0][index] = item1_stats[0][i]
        if item2_stats[0].count(item1_stats[0][i]) == 0:
            combined_stats[1][index] = item1_stats[1][i]
        else:
            index_in_item_2 = item2_stats[0].index(item1_stats[0][i])
            combined_stats[1][index] = item1_stats[1][i] + item2_stats[1][index_in_item_2]
        index += 1
    for i in range(len(item2_stats[0])):
        if item1_stats[0].count(item2_stats[0][i]) == 0:
            combined_stats[0][index] = item2_stats[0][i]
            combined_stats[1][index] = item2_stats[1][i]
        index += 1
    for i in range(len(combined_stats[0])-index):
        combined_stats[0].pop()
        combined_stats[1].pop()
    index = 0
    return combined_stats
    



def get_all_combinations(weapon_names, helmet_names, chestplate_names, legging_names, boot_names, ring_names, bracelet_names, necklace_names, weapon_data, helmet_data, chestplate_data, legging_data, boot_data, ring_data, bracelet_data, necklace_data, required_stats, best_amount):
    best_combinations: list = []
    for weapon_number in range(len(weapon_names)):
        for helmet_number in range(len(helmet_names)):
            wh_stats: tuple[list[str], list[int]] = combine_stats(weapon_data[weapon_number], helmet_data[helmet_number])
            for chestplate_number in range(len(chestplate_names)):
                whc_stats: tuple[list[str], list[int]] = combine_stats(wh_stats, chestplate_data[chestplate_number])
                for legging_number in range(len(legging_names)):
                    whcl_stats: tuple[list[str], list[int]] = combine_stats(whc_stats, legging_data[legging_number])
                    for boot_number in range(len(boot_names)):
                        whclb_stats: tuple[list[str], list[int]] = combine_stats(whcl_stats, boot_data[boot_number])
                        for ring1_number in range(len(ring_names)):
                            whclbr_stats: tuple[list[str], list[int]] = combine_stats(whclb_stats, ring_data[ring1_number])
                            for ring2_number in range(len(ring_names)):
                                whclbrr_stats: tuple[list[str], list[int]] = combine_stats(whclbr_stats, ring_data[ring2_number])
                                for bracelet_number in range(len(bracelet_names)):
                                    whclbrrba_stats: tuple[list[str], list[int]] = combine_stats(whclbrr_stats, bracelet_data[bracelet_number])
                                    for necklace_number in range(len(necklace_names)):
                                        whclbrrban_stats: tuple[list[str], list[int]] = combine_stats(whclbrrba_stats, necklace_data[necklace_number])
                                        possible = True
                                        sort_by_stat: str = ''
                                        for stat in required_stats[0]:
                                            if stat not in whclbrrban_stats[0]:
                                                possible = False
                                                break
                                            index_in_stats = whclbrrban_stats[0].index(stat)
                                            stat_value = whclbrrban_stats[1][index_in_stats]
                                            if required_stats[1][required_stats[0].index(stat)] is not None:
                                                if stat_value < required_stats[1][required_stats[0].index(stat)]:
                                                    possible = False
                                                    break
                                            else:
                                                sort_by_stat = stat
                                        if possible:
                                            combination_name = f'{weapon_names[weapon_number]} + {helmet_names[helmet_number]} + {chestplate_names[chestplate_number]} + {legging_names[legging_number]} + {boot_names[boot_number]} + {ring_names[ring1_number]} + {ring_names[ring2_number]} + {bracelet_names[bracelet_number]} + {necklace_names[necklace_number]}'
                                            best_combinations.append((combination_name, whclbrrban_stats))
                                            if len(best_combinations)>1:
                                                best_combination_names = [comb[0] for comb in best_combinations]
                                                best_combination_values = [comb[1] for comb in best_combinations]
                                                new_best_combination_names, best_combination_values = sort.sort_by_value(best_combination_names,best_combination_values, sort_by_stat)
                                                new_best_combinations = []
                                                for i in range(len(best_combination_names)):
                                                    new_best_combinations.append((new_best_combination_names[i], best_combinations[best_combination_names.index(new_best_combination_names[i])][1]))
                                                best_combinations = new_best_combinations
                                                #print(best_combination_names)
                                            if len(best_combinations) > best_amount:
                                                best_combinations = best_combinations[:best_amount]
                                            #comment to add a breakpoint
    try:
        return best_combinations
    except:
        print('something went wrong')
                                        
                                        


def listify_items(item_type: dict) -> tuple[list, list[tuple[list[str], list[int]]]]:
    parsed_data: tuple[list[str], list[dict]] = parse_items.make_lists_from_dicts(item_type)
    names = parsed_data[0]
    item_data = parsed_data[1]
    data_names: list = []
    data_values: list = []
    items_data: list[tuple[list[str], list[int]]] = [([], [])]
    for item in item_data:
        new_data_name, new_data_value = parse_items.make_lists_from_dicts(item)
        data_names.extend(new_data_name)
        data_values.extend(new_data_value)
        new_item_data: tuple[list[str], list[int]] = data_names, data_values
        data_names, data_values = [], []
        items_data.append(new_item_data)
    try:
        items_data.remove(([],[]))
    except:
        pass
    return names, items_data


def get_all_combinations_wrapper(inputs):
    output_list = []
    counter = 0
    for list in inputs:
        item_group = numba.typed.typedlist.List()
        for element in list:
            item_group.append(element)
        output_list[counter] = item_group
        counter += 1
    output = (output_list[0], output_list[1], output_list[2], output_list[3], output_list[4], output_list[5], output_list[6], output_list[7], output_list[8], output_list[9], output_list[10], output_list[11], output_list[12], output_list[13], output_list[14], output_list[15])
    return output


def main():
    item_lists = parse_items.parse_items()
    helmet_names, helmet_data = listify_items(item_lists[0])
    chestplate_names, chestplate_data = listify_items(item_lists[1])
    legging_names, legging_data = listify_items(item_lists[2])
    boot_names, boot_data = listify_items(item_lists[3])
    ring_names, ring_data = listify_items(item_lists[4])
    bracelet_names, bracelet_data = listify_items(item_lists[5])
    necklace_names, necklace_data = listify_items(item_lists[6])
    spear_names, spear_data = listify_items(item_lists[7])
    bow_names, bow_data = listify_items(item_lists[8])
    dagger_names, dagger_data = listify_items(item_lists[9])
    wand_names, wand_data = listify_items(item_lists[10])
    relik_names, relik_data = listify_items(item_lists[11])
    weapon_names = spear_names + bow_names + dagger_names + wand_names + relik_names
    weapon_data = spear_data + bow_data + dagger_data + wand_data + relik_data
    required_stats = parse_items.make_lists_from_dicts(get_required_stats_dict(get_stat_to_optimize()))
    #weapon_names, helmet_names, chestplate_names , legging_names, boot_names, ring_names, bracelet_names, necklace_names, weapon_data, helmet_data, chestplate_data, legging_data, boot_data, ring_data, bracelet_data, necklace_data = get_all_combinations_wrapper((weapon_names, helmet_names, chestplate_names, legging_names, boot_names, ring_names, bracelet_names, necklace_names, weapon_data, helmet_data, chestplate_data, legging_data, boot_data, ring_data, bracelet_data, necklace_data))
    combinations = get_all_combinations(weapon_names, helmet_names, chestplate_names, legging_names, boot_names, ring_names, bracelet_names, necklace_names, weapon_data, helmet_data, chestplate_data, legging_data, boot_data, ring_data, bracelet_data, necklace_data, required_stats, best_amount=10)

if __name__ == "__main__":
    main()