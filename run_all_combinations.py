# run_all_combinations.py
import numpy as np
from numba import njit, prange
from parse_items import load_items_from_json, make_required_stats_array, reconstruct_combination_name
from typing import Dict

# -------------------------
# Helper: produce index list of required stats in stat_order
# -------------------------
def required_indices_from_dict(required_stats: Dict[str, int], stat_order):
    # returns two things:
    # - req_idx: indices in stat_order that are present in required_stats (list[int])
    # - req_vals: corresponding required values (np.array, dtype=int64)
    idxs = []
    vals = []
    for i, s in enumerate(stat_order):
        if s in required_stats:
            idxs.append(i)
            vals.append(int(required_stats[s]))
    if len(idxs) == 0:
        # fallback: require nothing
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
    return np.array(idxs, dtype=np.int64), np.array(vals, dtype=np.int64)

# -------------------------
# Numba-compiled heavy loop
# Note: keep strictly typed arrays and simple python types
# -------------------------
@njit(parallel=True, cache=True)
def _find_best_combinations_numba(
    weapon_stats, helmet_stats, chest_stats, legging_stats,
    boot_stats, ring_stats, bracelet_stats, necklace_stats,
    req_idx_arr, req_vals_arr, best_amount
):
    # If any category empty -> return empty sentinel
    if (weapon_stats.shape[0] == 0 or helmet_stats.shape[0] == 0 or chest_stats.shape[0] == 0 or
        legging_stats.shape[0] == 0 or boot_stats.shape[0] == 0 or ring_stats.shape[0] == 0 or
        bracelet_stats.shape[0] == 0 or necklace_stats.shape[0] == 0):
        empty_scores = np.full(1, -9223372036854775808, dtype=np.int64)
        empty_combs = np.zeros((1, 9), dtype=np.int64)
        return empty_scores, empty_combs

    nw = weapon_stats.shape[0]
    nh = helmet_stats.shape[0]
    nc = chest_stats.shape[0]
    nl = legging_stats.shape[0]
    nb = boot_stats.shape[0]
    nr = ring_stats.shape[0]
    nba = bracelet_stats.shape[0]
    nn = necklace_stats.shape[0]

    # Keep top best_amount scores and their index tuples
    scores = np.full(best_amount, -9223372036854775808, dtype=np.int64)
    comb_idx = np.zeros((best_amount, 9), dtype=np.int64)

    # Local references for speed
    for i in prange(nw):
        ws = weapon_stats[i]
        # early pruning: check weapon alone
        ok = True
        for x in range(req_idx_arr.shape[0]):
            idx = req_idx_arr[x]
            if ws[idx] < req_vals_arr[x]:
                ok = False
                break
        if not ok:
            continue

        for j in range(nh):
            hs = helmet_stats[j]
            wh = ws + hs
            # prune
            ok = True
            for x in range(req_idx_arr.shape[0]):
                idx = req_idx_arr[x]
                if wh[idx] < req_vals_arr[x]:
                    ok = False
                    break
            if not ok:
                continue

            for k in range(nc):
                ch = chest_stats[k]
                whc = wh + ch
                ok = True
                for x in range(req_idx_arr.shape[0]):
                    idx = req_idx_arr[x]
                    if whc[idx] < req_vals_arr[x]:
                        ok = False
                        break
                if not ok:
                    continue

                for l in range(nl):
                    lg = legging_stats[l]
                    whcl = whc + lg
                    ok = True
                    for x in range(req_idx_arr.shape[0]):
                        idx = req_idx_arr[x]
                        if whcl[idx] < req_vals_arr[x]:
                            ok = False
                            break
                    if not ok:
                        continue

                    for m in range(nb):
                        bs = boot_stats[m]
                        whclb = whcl + bs
                        ok = True
                        for x in range(req_idx_arr.shape[0]):
                            idx = req_idx_arr[x]
                            if whclb[idx] < req_vals_arr[x]:
                                ok = False
                                break
                        if not ok:
                            continue

                        # rings (two slots) - naive double loop
                        for r1 in range(nr):
                            r1s = ring_stats[r1]
                            whclbr = whclb + r1s
                            ok = True
                            for x in range(req_idx_arr.shape[0]):
                                idx = req_idx_arr[x]
                                if whclbr[idx] < req_vals_arr[x]:
                                    ok = False
                                    break
                            if not ok:
                                continue

                            for r2 in range(nr):
                                r2s = ring_stats[r2]
                                whclbrr = whclbr + r2s
                                ok = True
                                for x in range(req_idx_arr.shape[0]):
                                    idx = req_idx_arr[x]
                                    if whclbrr[idx] < req_vals_arr[x]:
                                        ok = False
                                        break
                                if not ok:
                                    continue

                                for ba in range(nba):
                                    bas = bracelet_stats[ba]
                                    whclbrrba = whclbrr + bas
                                    ok = True
                                    for x in range(req_idx_arr.shape[0]):
                                        idx = req_idx_arr[x]
                                        if whclbrrba[idx] < req_vals_arr[x]:
                                            ok = False
                                            break
                                    if not ok:
                                        continue

                                    for nc_idx in range(nn):
                                        nks = necklace_stats[nc_idx]
                                        final = whclbrrba + nks
                                        ok = True
                                        for x in range(req_idx_arr.shape[0]):
                                            idx = req_idx_arr[x]
                                            if final[idx] < req_vals_arr[x]:
                                                ok = False
                                                break
                                        if not ok:
                                            continue

                                        # scoring: pick a simple score metric
                                        # We'll use sum of all required-stat values as score (fast and meaningful).
                                        score = 0
                                        for x in range(req_idx_arr.shape[0]):
                                            score += final[req_idx_arr[x]]

                                        # find minimum slot in top scores
                                        minpos = 0
                                        minval = scores[0]
                                        for t in range(1, best_amount):
                                            if scores[t] < minval:
                                                minval = scores[t]
                                                minpos = t

                                        if score > minval:
                                            # insert at minpos
                                            scores[minpos] = score
                                            comb_idx[minpos, 0] = i
                                            comb_idx[minpos, 1] = j
                                            comb_idx[minpos, 2] = k
                                            comb_idx[minpos, 3] = l
                                            comb_idx[minpos, 4] = m
                                            comb_idx[minpos, 5] = r1
                                            comb_idx[minpos, 6] = r2
                                            comb_idx[minpos, 7] = ba
                                            comb_idx[minpos, 8] = nc_idx

    return scores, comb_idx

# -------------------------
# Public API
# -------------------------
def run_all_combinations(json_path: str, required_stats: dict, best_amount: int = 10, use_gpu: bool = False):
    # Load everything using the parser
    items, structs = load_items_from_json(json_path)  # parse_items.py (your parser)
    stat_order = structs["stat_order"]

    # Build required indices/values arrays
    req_idx, req_vals = required_indices_from_dict(required_stats, stat_order)

    # If user wants GPU but cupy not present -> fallback
    """ if use_gpu:
        try:
            import cupy as cp
            # NOTE: GPU path is nontrivial for this combinatorial search; here we only fallback to CPU if not implemented.
            # For now we raise if user asked GPU but no implementation (future work: implement GPU kernels).
            raise RuntimeError("GPU mode requested but not implemented for full slot-structured search. Set use_gpu=False.")
        except ImportError:
            print("cupy not installed; running CPU (Numba) path.") """

    # Convert to numpy arrays for numba
    weapon_stats = structs["weapon_stats"].astype(np.int64)
    helmet_stats = structs["helmet_stats"].astype(np.int64)
    chest_stats = structs["chestplate_stats"].astype(np.int64)
    legging_stats = structs["legging_stats"].astype(np.int64)
    boot_stats = structs["boot_stats"].astype(np.int64)
    ring_stats = structs["ring_stats"].astype(np.int64)
    bracelet_stats = structs["bracelet_stats"].astype(np.int64)
    necklace_stats = structs["necklace_stats"].astype(np.int64)

    # Ensure required arrays are int64
    req_idx_arr = req_idx.astype(np.int64)
    req_vals_arr = req_vals.astype(np.int64)

    # Call Numba function
    scores, comb_indices = _find_best_combinations_numba(
        weapon_stats, helmet_stats, chest_stats, legging_stats,
        boot_stats, ring_stats, bracelet_stats, necklace_stats,
        req_idx_arr, req_vals_arr, best_amount
    )

    # If sentinel -> empty
    if scores.shape[0] == 1 and scores[0] == -9223372036854775808:
        return {}

    # Build readable results: reconstruct names and total stat dict (only required stats)
    results = {}
    for i in range(scores.shape[0]):
        if scores[i] == -9223372036854775808:
            continue
        idxs = comb_indices[i].astype(np.int64)
        name = reconstruct_combination_name(idxs, structs)
        # compute total stats vector (use numpy)
        total_vec = (
            weapon_stats[idxs[0]] + helmet_stats[idxs[1]] +
            chest_stats[idxs[2]] + legging_stats[idxs[3]] +
            boot_stats[idxs[4]] + ring_stats[idxs[5]] +
            ring_stats[idxs[6]] + bracelet_stats[idxs[7]] +
            necklace_stats[idxs[8]]
        )
        # Provide a dict for stat_order -> value (but to keep output small, return only required_stats and their totals)
        out = {}
        for x in range(req_idx_arr.shape[0]):
            sidx = req_idx_arr[x]
            out[stat_order[sidx]] = int(total_vec[sidx])
        results[name] = out

    return results


# If called standalone, basic example
if __name__ == "__main__":
    JSON_PATH = "items.json"
    REQUIRED_STATS = {"str": 50, "dex": 40}  # adapt to your stat names in stat_order
    BEST_AMOUNT = 10
    best = run_all_combinations(JSON_PATH, REQUIRED_STATS, BEST_AMOUNT, use_gpu=False)
    for k, v in best.items():
        print(k, v)
