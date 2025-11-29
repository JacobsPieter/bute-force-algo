# Cython version of main.py
# Converted from main.py with Cython optimizations for performance-critical functions.

import itertools
import numpy as np
cimport numpy as cnp
import heapq

# Constants remain as is
MAX_SKILL_POINTS: int = 595
MAX_STRREQ: int = 320
MAX_DEXREQ: int = 317
MAX_INTREQ: int = 283
MAX_DEFREQ: int = 284
MAX_AGIREQ: int = 333

cpdef bint skill_point_fast_check(const cnp.int64_t[:] stats, tuple required_stats):
    cdef int str_req = stats[required_stats[0]]
    cdef int dex_req = stats[required_stats[1]]
    cdef int int_req = stats[required_stats[2]]
    cdef int def_req = stats[required_stats[3]]
    cdef int agi_req = stats[required_stats[4]]
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

cpdef tuple combine(tuple combo1, tuple combo2):
    cdef cnp.ndarray[cnp.int64_t, ndim=1] combo1_values = combo1[1]
    cdef cnp.ndarray[cnp.int64_t, ndim=1] combo2_values = combo2[1]
    cdef cnp.ndarray[cnp.int64_t, ndim=1] resulting_stats = np.add(combo1_values, combo2_values)
    cdef str resulting_name = f'{combo1[0]}, {combo2[0]}'
    return resulting_name, resulting_stats

def precompute(items1, items2, skill_points_req_array_pos):
    combinations = itertools.product(items1, items2)
    for i, combination in enumerate(combinations):
        name_1, name_2 = combination[0][0], combination[1][0]
        combination_values_1, combination_values_2 = combination[0][1], combination[1][1]
        resulting_stats = np.add(combination_values_1, combination_values_2)
        resulting_name = f'{name_1}, {name_2}'
        if not skill_point_fast_check(resulting_stats, skill_points_req_array_pos):
            continue
        yield (resulting_name, resulting_stats)

cpdef list process_hccombo(tuple hccombo, list leggings_boots, list all_rings, list bracelets_necklaces, int stat_to_optimise, int max_best_length, int index, int total, tuple skill_points_req_array_pos):
    cdef list local_heap = []
    cdef int len_lb = len(leggings_boots)
    cdef int count = 0
    cdef tuple hclbcombo
    cdef tuple hclbrrcombo
    cdef tuple hclbrrbncombo
    cdef tuple final_combo
    cdef cnp.ndarray[cnp.int64_t, ndim=1] values
    cdef long long current_value
    print(f"Starting process {index}/{total} for combos")

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
                heapq.heappush(local_heap, (-current_value, final_combo))
                if len(local_heap) > max_best_length:
                    heapq.heappop(local_heap)
        count += 1
        if count % 20 == 0:
            print(f"Process {index}/{total}: {count}/{len_lb} leggings_boots processed")

    print(f"Process {index}/{total} completed")
    return [combo for _, combo in local_heap]
