# parse_items.py
import json
import numpy as np
from typing import Dict, Tuple, List

def parse_stat_value(value):
    """
    Convert any JSON stat value into a single numeric value.
    - ints/floats -> int
    - lists -> sum of numeric entries (ignore non-numeric)
    - booleans -> int(value)
    - strings -> 0
    - None -> 0
    """
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, list):
        total = 0
        for v in value:
            try:
                total += int(v)
            except (ValueError, TypeError):
                continue
        return total
    # strings or other types -> 0
    return 0


def load_items_from_json(json_path: str) -> Tuple[List[Dict], Dict]:
    """
    Load items.json and build numpy arrays (int64) per slot + name lists + stat_order.
    Expected items.json structure: {"items": [ <item dicts> ] }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])

    # Determine stat keys (exclude metadata keys)
    skip_keys = {"name", "id", "category", "type", "drop", "lore", "icon", "tier", "displayName", "dropInfo"}
    stat_keys = set()
    for item in items:
        for k in item.keys():
            if k not in skip_keys:
                stat_keys.add(k)
    stat_order = list(stat_keys)

    # Slot mapping: depends on how items label type/category in your JSON.
    # These are the slot types this project expects; change if your JSON uses other strings.
    slots = ["weapon", "helmet", "chestplate", "leggings", "boots", "ring", "bracelet", "necklace"]

    arrays = {}
    names = {}

    # For each slot, collect items whose 'type' equals slot OR whose 'category' equals slot.
    for slot in slots:
        slot_items = [it for it in items if (it.get("type") == slot or it.get("category") == slot)]
        n = len(slot_items)
        stats_arr = np.zeros((n, len(stat_order)), dtype=np.int64)
        name_list = []
        for i, it in enumerate(slot_items):
            name_list.append(it.get("name", f"{slot}_{i}"))
            for si, stat in enumerate(stat_order):
                raw = it.get(stat, 0)
                stats_arr[i, si] = parse_stat_value(raw)
        arrays[f"{slot}_stats"] = stats_arr
        names[f"{slot}_names"] = name_list

    # Special: rings are two slots in final combination; we'll reuse ring_stats for both ring slots.
    # Return stat_order so caller can map stat names to indices.
    structs = {**arrays, **names, "stat_order": stat_order}
    return items, structs


def make_required_stats_array(required_stats: dict, stat_order: list) -> np.ndarray:
    arr = np.zeros(len(stat_order), dtype=np.int64)
    for idx, stat in enumerate(stat_order):
        if stat in required_stats:
            try:
                arr[idx] = int(required_stats[stat])
            except (ValueError, TypeError):
                arr[idx] = 0
    return arr


def reconstruct_combination_name(indices: np.ndarray, structs: Dict) -> str:
    """
    indices: array-like length 9: [weapon,helmet,chest,legging,boot,ring1,ring2,bracelet,necklace]
    """
    try:
        return (
            f"{structs['weapon_names'][int(indices[0])]} + "
            f"{structs['helmet_names'][int(indices[1])]} + "
            f"{structs['chestplate_names'][int(indices[2])]} + "
            f"{structs['legging_names'][int(indices[3])]} + "
            f"{structs['boot_names'][int(indices[4])]} + "
            f"{structs['ring_names'][int(indices[5])]} + "
            f"{structs['ring_names'][int(indices[6])]} + "
            f"{structs['bracelet_names'][int(indices[7])]} + "
            f"{structs['necklace_names'][int(indices[8])]}"
        )
    except Exception:
        return "Invalid combination"
