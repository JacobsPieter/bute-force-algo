import parser
import human_readable_stat_names_and_indices as names_and_indices

import itertools
import numpy as np
from numba import njit
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import heapq
import time



BENCHMARK = True  # Set to False to use interactive input
SINGLE_THREADED = False  # Set to True to disable multiprocessing

MAX_SKILL_POINTS: int = 595
MAX_STRREQ: int = 320
MAX_DEXREQ: int = 317
MAX_INTREQ: int = 283
MAX_DEFREQ: int = 284
MAX_AGIREQ: int = 333


def get_stat_to_optimise():
    if BENCHMARK:
        return names_and_indices.STAT_INDICES['hp']
    else:
        new_input = input('Give stat to optimize: ')
        new_input.strip().lower()
        return names_and_indices.STAT_INDICES[new_input]

def get_max_best_length():
    if BENCHMARK:
        return 10  # small for quick benchmarks
    else:
        new_input = input('Give the max amount of best results to give (lower = faster): ')
        numerical_input = int(new_input.strip().lower())
        return numerical_input

@njit
def skill_point_fast_check(stats: np.ndarray, required_stats: tuple[int, int, int, int, int]) -> bool:
    str_req = stats[required_stats[0]]
    dex_req = stats[required_stats[1]]
    int_req = stats[required_stats[2]]
    def_req = stats[required_stats[3]]
    agi_req = stats[required_stats[4]]
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


@njit
def combine(combo1: tuple[str, np.ndarray], combo2: tuple[str, np.ndarray]):
    combo1_values = combo1[1]
    combo2_values = combo2[1]
    resulting_stats = np.add(combo1_values, combo2_values)
    resulting_name = f'{combo1[0]}, {combo2[0]}'
    return resulting_name, resulting_stats



def precompute(items1: list[tuple[str, np.ndarray]], items2: list[tuple[str, np.ndarray]], skill_points_req_array_pos: tuple):
    combinations = itertools.product(items1, items2)
    for i, combination in enumerate(combinations):
        name_1, name_2 = combination[0][0], combination[1][0]
        combination_values_1, combination_values_2 = combination[0][1], combination[1][1]
        resulting_stats = np.add(combination_values_1, combination_values_2)
        resulting_name = f'{name_1}, {name_2}'
        if not skill_point_fast_check(resulting_stats, skill_points_req_array_pos):
            continue
        yield (resulting_name, resulting_stats)



def dict_from_map_object(to_convert) -> dict[str, dict[str, int]]:
    converted = {}
    for dictionary in to_convert:
        converted.update(dictionary)
    return converted



def process_hccombo_wrapper(hccombo, leggings_boots, all_rings, bracelets_necklaces, stat_to_optimise, max_best_length, index, total, skill_points_req_array_pos: tuple):
    print(f'starting process {index}/{total}')
    #precompile_numba()
    return process_hccombo(hccombo, leggings_boots, all_rings, bracelets_necklaces, stat_to_optimise, max_best_length, index, total, skill_points_req_array_pos)








@njit
def process_hccombo(hccombo, leggings_boots, all_rings, bracelets_necklaces, stat_to_optimise, max_best_length, index, total, skill_points_req_array_pos: tuple):
    # Initialize top list with dummy low values
    dummy_stats = np.full(108, -999999, dtype=np.int64)
    dummy_combo = ('dummy', dummy_stats)
    local_top = [dummy_combo] * max_best_length
    local_values = [-999999] * max_best_length

    for lbcombo in leggings_boots:
        hclbcombo = combine(hccombo, lbcombo)
        if not skill_point_fast_check(hclbcombo[1], skill_points_req_array_pos):
            continue
        for rrcombo in all_rings:
            hclbrrcombo = combine(hclbcombo, rrcombo)
            if not skill_point_fast_check(hclbrrcombo[1], skill_points_req_array_pos):
                continue
            for bncombo in bracelets_necklaces:
                hclbrrbncombo = combine(hclbrrcombo, bncombo)
                final_combo = hclbrrbncombo
                values = final_combo[1]
                if not skill_point_fast_check(values, skill_points_req_array_pos):
                    continue
                current_value = values[stat_to_optimise]
                # Find the min in local_values
                min_val = min(local_values)
                if current_value > min_val:
                    # Replace the one with min_val
                    idx = local_values.index(min_val)
                    local_top[idx] = final_combo
                    local_values[idx] = current_value

    # Bubble sort local_top by local_values descending
    for i in range(max_best_length):
        for j in range(i + 1, max_best_length):
            if local_values[j] > local_values[i]:
                # Swap
                local_values[i], local_values[j] = local_values[j], local_values[i]
                local_top[i], local_top[j] = local_top[j], local_top[i]

    return local_top




def get_permutations(database_path):
    stat_to_optimise = get_stat_to_optimise()
    max_best_length = get_max_best_length()

    print('started running. Please wait ...')

    skill_points_req_array_pos = (names_and_indices.STAT_INDICES["strength"], names_and_indices.STAT_INDICES["dexterity"], names_and_indices.STAT_INDICES["intelligence"], names_and_indices.STAT_INDICES["defense"], names_and_indices.STAT_INDICES["agility"])

    items = parser.parse_items(database_path)
    helmets, chestplates, leggings, boots, rings, bracelets, necklaces, spears, bows, daggers, wands, reliks = items
    weapons = spears + bows + daggers + wands + reliks

    helmets_chestplates = [x for x in precompute(helmets, chestplates, skill_points_req_array_pos)]
    leggings_boots = [x for x in precompute(leggings, boots, skill_points_req_array_pos)]
    all_rings = [x for x in precompute(rings, rings, skill_points_req_array_pos)]
    bracelets_necklaces = [x for x in precompute(bracelets, necklaces, skill_points_req_array_pos)]

    start_time = time.time()
    if SINGLE_THREADED:
        # Single-threaded processing
        all_results = []
        total = len(helmets_chestplates)
        precompile_numba()
        for index, hccombo in enumerate(helmets_chestplates):
            print(f'Progress: {index + 1}/{total} combinations started')
            result = process_hccombo(hccombo, leggings_boots, all_rings, bracelets_necklaces, stat_to_optimise, max_best_length, index + 1, total, skill_points_req_array_pos)
            all_results.extend(result)
            print(f"Progress: {index + 1}/{total} combinations processed")

        # Sort final results
        all_results.sort(key=lambda x: x[1][stat_to_optimise], reverse=True)
        best_list = all_results[:max_best_length]
    else:
        # Multiprocessing version
        precompile_numba()
        with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
            # Submit all hccombo processing tasks
            futures = []
            for index, hccombo in enumerate(helmets_chestplates):
                future = executor.submit(
                    process_hccombo_wrapper,
                    hccombo,
                    leggings_boots,
                    all_rings,
                    bracelets_necklaces,
                    stat_to_optimise,
                    max_best_length,
                    index + 1,
                    len(helmets_chestplates),
                    skill_points_req_array_pos
                )
                futures.append(future)
            # Collect results from all workers
            all_results = []
            total = len(futures)
            done = 0
            for future in futures:
                all_results.extend(future.result())
                done += 1
                print(f"Progress: {done}/{total} combinations processed")

            # Merge and sort final results
            all_results.sort(key=lambda x: x[1][stat_to_optimise], reverse=True)
            best_list = all_results[:max_best_length]

    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
    return best_list

                    


def precompile_numba():
    print('compiling functions')
    print('this might take a while...')
    # Precompile Numba functions
    skill_point_fast_check(np.zeros(108, dtype=np.int64), (0,1,2,3,4))
    combine(('test', np.zeros(108)), ('test', np.zeros(108)))
    # Precompile process_hccombo
    dummy_combo = ('test', np.zeros(108, dtype=np.int64))
    dummy_list = [dummy_combo]
    process_hccombo(dummy_combo, dummy_list, dummy_list, dummy_list, 0, 1, 1, 1, (0,1,2,3,4))
    print('Done!')














def main():
    precompile_numba()
    database_path = "data\\items.json"
    get_permutations(database_path)



if __name__ == "__main__":
    main()
