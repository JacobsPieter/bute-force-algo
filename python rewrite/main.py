import parser
import human_readable_stat_names_and_indices as names_and_indices

import itertools
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import time

# Import Cython optimized functions
from cython_main import skill_point_fast_check, combine, precompute, process_hccombo



BENCHMARK = True  # Set to False to use interactive input

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
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        # Submit all hccombo processing tasks
        futures = []
        for index, hccombo in enumerate(helmets_chestplates):
            future = executor.submit(
                process_hccombo,
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
    combine(('test', np.zeros(108, dtype=np.int64)), ('test', np.zeros(108, dtype=np.int64)))
    print('Done!')














def main():
    precompile_numba()
    database_path = "../data/items.json"
    get_permutations(database_path)



if __name__ == "__main__":
    main()
