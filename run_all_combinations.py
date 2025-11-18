# run_all_combinations.py
import numpy as np
from numba import njit, prange
from parse_items import load_items_from_json, reconstruct_combination_name
from typing import Dict, List, Tuple

SLOT_ORDER = ["weapon", "helmet", "chestplate", "legging", "boot", "ring", "ring", "bracelet", "necklace"]

# Helpers to map stat names -> indices and build arrays for Numba
def _stat_index_map(stat_order: List[str]) -> Dict[str, int]:
    return {name: i for i, name in enumerate(stat_order)}

def _build_minreq_arrays(min_requirements: Dict[str, int], stat_index_map: Dict[str, int]) -> Tuple[np.ndarray, np.ndarray]:
    if not min_requirements:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
    idxs = []
    vals = []
    for k, v in min_requirements.items():
        if k in stat_index_map:
            try:
                val = int(v)
            except (TypeError, ValueError):
                val = 0
            idxs.append(stat_index_map[k])
            vals.append(val)
    return np.array(idxs, dtype=np.int64), np.array(vals, dtype=np.int64)

def _build_weights_array(maximize: str, maximize_weights: Dict[str, float], stat_order: List[str]) -> Tuple[int, np.ndarray]:
    """
    Returns (maximize_idx_or_-1, weights_array_float64_of_len_nstats)
    maximize (single stat name) can be None
    maximize_weights can be empty or have keys mapping to stat_order names
    """
    n = len(stat_order)
    weights = np.zeros(n, dtype=np.float64)
    if maximize_weights:
        for k, w in maximize_weights.items():
            if k in stat_order:
                try:
                    weights[stat_order.index(k)] = float(w)
                except:
                    weights[stat_order.index(k)] = 0.0
    maximize_idx = -1
    if maximize and maximize in stat_order:
        maximize_idx = stat_order.index(maximize)
    return maximize_idx, weights

# -------------------------------
# Numba kernel
# returns (scores_float64_array_topN, comb_indices_int64_array_topNx9)
# sentinel empty: scores array length 1 with very negative value
# -------------------------------
@njit(parallel=True, cache=True)
def _search_numba(
    weapon_stats, helmet_stats, chest_stats, legging_stats,
    boot_stats, ring_stats, bracelet_stats, necklace_stats,
    skill_idx_arr, req_idx_arr, required_skill_vals,
    slot_max_skill, total_max_skill,
    minreq_idx_arr, minreq_val_arr,
    maximize_idx, weight_arr,
    best_n
):
    # If any category empty => return empty sentinel
    if (weapon_stats.shape[0] == 0 or helmet_stats.shape[0] == 0 or chest_stats.shape[0] == 0 or
        legging_stats.shape[0] == 0 or boot_stats.shape[0] == 0 or ring_stats.shape[0] == 0 or
        bracelet_stats.shape[0] == 0 or necklace_stats.shape[0] == 0):
        empty_scores = np.full(1, -1e300, dtype=np.float64)
        empty_idx = np.zeros((1, 9), dtype=np.int64)
        return empty_scores, empty_idx

    nw = weapon_stats.shape[0]
    nh = helmet_stats.shape[0]
    nc = chest_stats.shape[0]
    nl = legging_stats.shape[0]
    nb = boot_stats.shape[0]
    nr = ring_stats.shape[0]
    nba = bracelet_stats.shape[0]
    nn = necklace_stats.shape[0]
    nskills = skill_idx_arr.shape[0]
    nstats = weapon_stats.shape[1]

    scores = np.full(best_n, -1e300, dtype=np.float64)
    comb_idx = np.zeros((best_n, 9), dtype=np.int64)

    # Outer loops parallelizable on weapon
    for i in prange(nw):
        ws = weapon_stats[i]
        # partial skill totals (for the 5 skill stats)
        partial_skill = np.zeros(nskills, dtype=np.int64)
        for s in range(nskills):
            si = skill_idx_arr[s]
            if si != -1:
                partial_skill[s] = ws[si]
            else:
                partial_skill[s] = 0
        # selected max sum: start with weapon slot's max
        selected_max = np.zeros(nskills, dtype=np.int64)
        for s in range(nskills):
            selected_max[s] = slot_max_skill[0, s]
        remaining_max = np.zeros(nskills, dtype=np.int64)
        for s in range(nskills):
            remaining_max[s] = total_max_skill[s] - selected_max[s]

        # SP-based prune: if even assuming maximal remaining, required_skill_vals cannot be reached -> skip
        impossible = False
        for s in range(nskills):
            if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                impossible = True
                break
        if impossible:
            continue

        for j in range(nh):
            hs = helmet_stats[j]
            for s in range(nskills):
                si = skill_idx_arr[s]
                if si != -1:
                    partial_skill[s] += hs[si]
            for s in range(nskills):
                selected_max[s] += slot_max_skill[1, s]
                remaining_max[s] = total_max_skill[s] - selected_max[s]
            # prune
            imp = False
            for s in range(nskills):
                if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                    imp = True
                    break
            if imp:
                for s in range(nskills):
                    si = skill_idx_arr[s]
                    if si != -1:
                        partial_skill[s] -= hs[si]
                    selected_max[s] -= slot_max_skill[1, s]
                    remaining_max[s] = total_max_skill[s] - selected_max[s]
                continue

            for k in range(nc):
                ch = chest_stats[k]
                for s in range(nskills):
                    si = skill_idx_arr[s]
                    if si != -1:
                        partial_skill[s] += ch[si]
                for s in range(nskills):
                    selected_max[s] += slot_max_skill[2, s]
                    remaining_max[s] = total_max_skill[s] - selected_max[s]
                imp2 = False
                for s in range(nskills):
                    if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                        imp2 = True
                        break
                if imp2:
                    for s in range(nskills):
                        si = skill_idx_arr[s]
                        if si != -1:
                            partial_skill[s] -= ch[si]
                        selected_max[s] -= slot_max_skill[2, s]
                        remaining_max[s] = total_max_skill[s] - selected_max[s]
                    continue

                for l in range(nl):
                    lg = legging_stats[l]
                    for s in range(nskills):
                        si = skill_idx_arr[s]
                        if si != -1:
                            partial_skill[s] += lg[si]
                    for s in range(nskills):
                        selected_max[s] += slot_max_skill[3, s]
                        remaining_max[s] = total_max_skill[s] - selected_max[s]
                    imp3 = False
                    for s in range(nskills):
                        if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                            imp3 = True
                            break
                    if imp3:
                        for s in range(nskills):
                            si = skill_idx_arr[s]
                            if si != -1:
                                partial_skill[s] -= lg[si]
                            selected_max[s] -= slot_max_skill[3, s]
                            remaining_max[s] = total_max_skill[s] - selected_max[s]
                        continue

                    for m in range(nb):
                        bs = boot_stats[m]
                        for s in range(nskills):
                            si = skill_idx_arr[s]
                            if si != -1:
                                partial_skill[s] += bs[si]
                        for s in range(nskills):
                            selected_max[s] += slot_max_skill[4, s]
                            remaining_max[s] = total_max_skill[s] - selected_max[s]
                        imp4 = False
                        for s in range(nskills):
                            if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                                imp4 = True
                                break
                        if imp4:
                            for s in range(nskills):
                                si = skill_idx_arr[s]
                                if si != -1:
                                    partial_skill[s] -= bs[si]
                                selected_max[s] -= slot_max_skill[4, s]
                                remaining_max[s] = total_max_skill[s] - selected_max[s]
                            continue

                        for r1 in range(nr):
                            r1s = ring_stats[r1]
                            for s in range(nskills):
                                si = skill_idx_arr[s]
                                if si != -1:
                                    partial_skill[s] += r1s[si]
                            for s in range(nskills):
                                selected_max[s] += slot_max_skill[5, s]
                                remaining_max[s] = total_max_skill[s] - selected_max[s]
                            imp5 = False
                            for s in range(nskills):
                                if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                                    imp5 = True
                                    break
                            if imp5:
                                for s in range(nskills):
                                    si = skill_idx_arr[s]
                                    if si != -1:
                                        partial_skill[s] -= r1s[si]
                                    selected_max[s] -= slot_max_skill[5, s]
                                    remaining_max[s] = total_max_skill[s] - selected_max[s]
                                continue

                            for r2 in range(nr):
                                r2s = ring_stats[r2]
                                for s in range(nskills):
                                    si = skill_idx_arr[s]
                                    if si != -1:
                                        partial_skill[s] += r2s[si]
                                for s in range(nskills):
                                    selected_max[s] += slot_max_skill[6, s]
                                    remaining_max[s] = total_max_skill[s] - selected_max[s]
                                imp6 = False
                                for s in range(nskills):
                                    if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                                        imp6 = True
                                        break
                                if imp6:
                                    for s in range(nskills):
                                        si = skill_idx_arr[s]
                                        if si != -1:
                                            partial_skill[s] -= r2s[si]
                                        selected_max[s] -= slot_max_skill[6, s]
                                        remaining_max[s] = total_max_skill[s] - selected_max[s]
                                    continue

                                for ba in range(nba):
                                    bas = bracelet_stats[ba]
                                    for s in range(nskills):
                                        si = skill_idx_arr[s]
                                        if si != -1:
                                            partial_skill[s] += bas[si]
                                    for s in range(nskills):
                                        selected_max[s] += slot_max_skill[7, s]
                                        remaining_max[s] = total_max_skill[s] - selected_max[s]
                                    imp7 = False
                                    for s in range(nskills):
                                        if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                                            imp7 = True
                                            break
                                    if imp7:
                                        for s in range(nskills):
                                            si = skill_idx_arr[s]
                                            if si != -1:
                                                partial_skill[s] -= bas[si]
                                            selected_max[s] -= slot_max_skill[7, s]
                                            remaining_max[s] = total_max_skill[s] - selected_max[s]
                                        continue

                                    for nc_i in range(nn):
                                        nks = necklace_stats[nc_i]
                                        for s in range(nskills):
                                            si = skill_idx_arr[s]
                                            if si != -1:
                                                partial_skill[s] += nks[si]
                                        for s in range(nskills):
                                            selected_max[s] += slot_max_skill[8, s]
                                            remaining_max[s] = total_max_skill[s] - selected_max[s]
                                        # final SP feasibility check:
                                        impossible_final = False
                                        for s in range(nskills):
                                            if partial_skill[s] + remaining_max[s] < required_skill_vals[s]:
                                                impossible_final = True
                                                break
                                        if impossible_final:
                                            for s in range(nskills):
                                                si = skill_idx_arr[s]
                                                if si != -1:
                                                    partial_skill[s] -= nks[si]
                                                selected_max[s] -= slot_max_skill[8, s]
                                                remaining_max[s] = total_max_skill[s] - selected_max[s]
                                            continue

                                        # Now we have a FULL build. We must:
                                        # 1) Check per-item requirements (if req_idx_arr has indices)
                                        # 2) Check min_requirements (stat-based) if present
                                        # 3) Compute score based on maximize_idx and weight_arr
                                        # Compute final totals (for all stats)
                                        final_totals = np.zeros(nstats, dtype=np.int64)
                                        # sum columns from each selected item
                                        # fetch each slot's stat row and add
                                        # weapon i
                                        for c in range(nstats):
                                            final_totals[c] = 0
                                        for c in range(nstats):
                                            final_totals[c] += weapon_stats[i, c]
                                            final_totals[c] += helmet_stats[j, c]
                                            final_totals[c] += chest_stats[k, c]
                                            final_totals[c] += legging_stats[l, c]
                                            final_totals[c] += boot_stats[m, c]
                                            final_totals[c] += ring_stats[r1, c]
                                            final_totals[c] += ring_stats[r2, c]
                                            final_totals[c] += bracelet_stats[ba, c]
                                            final_totals[c] += necklace_stats[nc_i, c]

                                        # per-item requirements check (req_idx_arr holds indices for skill req columns or -1)
                                        valid_items = True
                                        # For each skill index (like strReq), if req_idx_arr[s] != -1 then
                                        # for each slot verify final_totals[skill_idx] >= item_req_value at that slot
                                        for s in range(req_idx_arr.shape[0]):
                                            rr = req_idx_arr[s]
                                            if rr == -1:
                                                continue
                                            # weapon req
                                            if final_totals[s] < weapon_stats[i, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < helmet_stats[j, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < chest_stats[k, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < legging_stats[l, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < boot_stats[m, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < ring_stats[r1, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < ring_stats[r2, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < bracelet_stats[ba, rr]:
                                                valid_items = False
                                                break
                                            if final_totals[s] < necklace_stats[nc_i, rr]:
                                                valid_items = False
                                                break
                                        if not valid_items:
                                            for s in range(nskills):
                                                si = skill_idx_arr[s]
                                                if si != -1:
                                                    partial_skill[s] -= nks[si]
                                                selected_max[s] -= slot_max_skill[8, s]
                                                remaining_max[s] = total_max_skill[s] - selected_max[s]
                                            continue

                                        # min_requirements (stat-based) check
                                        meets_minreq = True
                                        for mr in range(minreq_idx_arr.shape[0]):
                                            midx = minreq_idx_arr[mr]
                                            if final_totals[midx] < minreq_val_arr[mr]:
                                                meets_minreq = False
                                                break
                                        if not meets_minreq:
                                            for s in range(nskills):
                                                si = skill_idx_arr[s]
                                                if si != -1:
                                                    partial_skill[s] -= nks[si]
                                                selected_max[s] -= slot_max_skill[8, s]
                                                remaining_max[s] = total_max_skill[s] - selected_max[s]
                                            continue

                                        # compute score (float64)
                                        score = 0.0
                                        if maximize_idx != -1:
                                            score += float(final_totals[maximize_idx])
                                        for st in range(nstats):
                                            score += weight_arr[st] * float(final_totals[st])

                                        # insert into top-N (min-heap replacement)
                                        minpos = 0
                                        minval = scores[0]
                                        for t in range(1, best_n):
                                            if scores[t] < minval:
                                                minval = scores[t]
                                                minpos = t
                                        if score > minval:
                                            scores[minpos] = score
                                            comb_idx[minpos, 0] = i
                                            comb_idx[minpos, 1] = j
                                            comb_idx[minpos, 2] = k
                                            comb_idx[minpos, 3] = l
                                            comb_idx[minpos, 4] = m
                                            comb_idx[minpos, 5] = r1
                                            comb_idx[minpos, 6] = r2
                                            comb_idx[minpos, 7] = ba
                                            comb_idx[minpos, 8] = nc_i

                                        # revert necklace totals
                                        for s in range(nskills):
                                            si = skill_idx_arr[s]
                                            if si != -1:
                                                partial_skill[s] -= nks[si]
                                            selected_max[s] -= slot_max_skill[8, s]
                                            remaining_max[s] = total_max_skill[s] - selected_max[s]

                                    # revert bracelet
                                    for s in range(nskills):
                                        si = skill_idx_arr[s]
                                        if si != -1:
                                            partial_skill[s] -= bas[si]
                                        selected_max[s] -= slot_max_skill[7, s]
                                        remaining_max[s] = total_max_skill[s] - selected_max[s]

                                # revert ring2
                                for s in range(nskills):
                                    si = skill_idx_arr[s]
                                    if si != -1:
                                        partial_skill[s] -= r2s[si]
                                    selected_max[s] -= slot_max_skill[6, s]
                                    remaining_max[s] = total_max_skill[s] - selected_max[s]

                            # revert ring1
                            for s in range(nskills):
                                si = skill_idx_arr[s]
                                if si != -1:
                                    partial_skill[s] -= r1s[si]
                                selected_max[s] -= slot_max_skill[5, s]
                                remaining_max[s] = total_max_skill[s] - selected_max[s]

                        # revert boots
                        for s in range(nskills):
                            si = skill_idx_arr[s]
                            if si != -1:
                                partial_skill[s] -= bs[si]
                            selected_max[s] -= slot_max_skill[4, s]
                            remaining_max[s] = total_max_skill[s] - selected_max[s]

                    # revert legging
                    for s in range(nskills):
                        si = skill_idx_arr[s]
                        if si != -1:
                            partial_skill[s] -= lg[si]
                        selected_max[s] -= slot_max_skill[3, s]
                        remaining_max[s] = total_max_skill[s] - selected_max[s]

                # revert chest
                for s in range(nskills):
                    si = skill_idx_arr[s]
                    if si != -1:
                        partial_skill[s] -= ch[si]
                    selected_max[s] -= slot_max_skill[2, s]
                    remaining_max[s] = total_max_skill[s] - selected_max[s]

            # revert helmet
            for s in range(nskills):
                si = skill_idx_arr[s]
                if si != -1:
                    partial_skill[s] -= hs[si]
                selected_max[s] -= slot_max_skill[1, s]
                remaining_max[s] = total_max_skill[s] - selected_max[s]

        # end weapon loop

    return scores, comb_idx

# -------------------------------
# Public API
# -------------------------------
def run_all_combinations(
    json_path: str,
    min_requirements: Dict[str, int] = {},
    maximize: str = '',
    maximize_weights: Dict[str, float] = {},
    top_n: int = 10,
    use_gpu: bool = False
):
    """
    Params:
      - min_requirements: map stat_name -> min_value (filter mode)
      - maximize: single stat name to maximize (Mode A) or None
      - maximize_weights: dict stat_name -> float weight (Mode B)
      - top_n: how many best builds to keep
    """
    if min_requirements == {}:
        min_requirements = {}
    if maximize_weights == {}:
        maximize_weights = {}

    items, structs = load_items_from_json(json_path)
    stat_order = structs["stat_order"]
    stat_map = _stat_index_map(stat_order)

    # Skill indices for pruning: 'str','dex','int','def','agi' (use -1 if missing)
    skill_names = ["str", "dex", "int", "def", "agi"]
    skill_idx = []
    for s in skill_names:
        skill_idx.append(stat_map.get(s, -1))
    skill_idx_arr = np.array(skill_idx, dtype=np.int64)

    # req idx arr: 'strReq', 'dexReq', ...
    req_idx = []
    for s in skill_names:
        req_idx.append(stat_map.get(s + "Req", -1))
    req_idx_arr = np.array(req_idx, dtype=np.int64)

    # required_skill_vals (the *socketed* required skill thresholds passed by user; we default to zero)
    required_skill_vals = np.zeros(len(skill_idx_arr), dtype=np.int64)
    for i, s in enumerate(skill_names):
        required_skill_vals[i] = int(min_requirements.get(s, 0))

    # Build min_requirements arrays (stat-based filters)
    minreq_idx_arr, minreq_val_arr = _build_minreq_arrays(min_requirements, stat_map)

    # Build maximize idx and weight array
    maximize_idx, weight_arr = _build_weights_array(maximize, maximize_weights, stat_order)

    # Precompute slot_max_skill and total_max_skill (shape (9, nskills) and (nskills,))
    def _slot_max_for(key: str):
        arr = structs.get(f"{key}_stats")
        if arr is None or arr.shape[0] == 0:
            return np.zeros(len(skill_idx_arr), dtype=np.int64)
        out = np.zeros(len(skill_idx_arr), dtype=np.int64)
        for si in range(len(skill_idx_arr)):
            idx = skill_idx_arr[si]
            if idx == -1:
                out[si] = 0
            else:
                out[si] = int(np.max(arr[:, idx].astype(np.int64))) if arr.shape[0] > 0 else 0
        return out

    slot_max = np.zeros((9, len(skill_idx_arr)), dtype=np.int64)
    for s_i, slot in enumerate(SLOT_ORDER):
        slot_key = slot
        slot_max[s_i, :] = _slot_max_for(slot_key)
    total_max_skill = np.zeros(len(skill_idx_arr), dtype=np.int64)
    for si in range(len(skill_idx_arr)):
        ssum = 0
        for r in range(slot_max.shape[0]):
            ssum += int(slot_max[r, si])
        total_max_skill[si] = ssum

    # Cast arrays to int64/float64 for numba
    weapon_stats = structs["weapon_stats"].astype(np.int64)
    helmet_stats = structs["helmet_stats"].astype(np.int64)
    chest_stats = structs["chestplate_stats"].astype(np.int64)
    legging_stats = structs["legging_stats"].astype(np.int64)
    boot_stats = structs["boot_stats"].astype(np.int64)
    ring_stats = structs["ring_stats"].astype(np.int64)
    bracelet_stats = structs["bracelet_stats"].astype(np.int64)
    necklace_stats = structs["necklace_stats"].astype(np.int64)

    # call numba search
    scores, comb_idx = _search_numba(
        weapon_stats, helmet_stats, chest_stats, legging_stats,
        boot_stats, ring_stats, bracelet_stats, necklace_stats,
        skill_idx_arr.astype(np.int64), req_idx_arr.astype(np.int64), required_skill_vals.astype(np.int64),
        slot_max.astype(np.int64), total_max_skill.astype(np.int64),
        minreq_idx_arr.astype(np.int64), minreq_val_arr.astype(np.int64),
        np.int64(maximize_idx), weight_arr.astype(np.float64),
        int(top_n)
    )

    # sentinel check
    if scores.shape[0] == 1 and scores[0] < -1e200:
        return {}

    # Build readable results
    results = {}
    # Convert stat_order to list of names to present totals
    for t in range(scores.shape[0]):
        if scores[t] < -1e200:
            continue
        idxs = comb_idx[t].astype(np.int64)
        name = reconstruct_combination_name(idxs, structs)
        # compute final totals for stat_order
        total_vec = (
            weapon_stats[int(idxs[0])] + helmet_stats[int(idxs[1])] +
            chest_stats[int(idxs[2])] + legging_stats[int(idxs[3])] +
            boot_stats[int(idxs[4])] + ring_stats[int(idxs[5])] +
            ring_stats[int(idxs[6])] + bracelet_stats[int(idxs[7])] +
            necklace_stats[int(idxs[8])]
        )
        # map stat_order -> int value
        out = {}
        for si, name_stat in enumerate(stat_order):
            out[name_stat] = int(total_vec[si])
        # include score for sorting/inspection
        out["_score"] = float(scores[t])
        results[name] = out

    return results


if __name__ == "__main__":
    # quick test (adjust stat names to those in your stat_order)
    res = run_all_combinations("items.json", min_requirements={"str": 0}, maximize="sdRaw", maximize_weights={"sdRaw":1.0}, top_n=5)
    for k, v in res.items():
        print(k, v["_score"])
