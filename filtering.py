

def filter_combinations_by_stat(combinations: dict[str, dict[str, int]], stat: str, min_value) -> dict[str, dict[str, int]]:
    filtered: dict[str, dict[str, int]] = {}
    for combo_name, stats in combinations.items():
        if stat in stats:
            if min_value == -1:
                filtered[combo_name] = stats
                continue
            if stats[stat] >= min_value:
                filtered[combo_name] = stats
    return filtered




def filter(combinations: dict[str, dict[str, int]], required_stats: dict[str, int]) -> dict[str, dict[str, int]]:
    new_combinations = combinations.copy()
    for stat in required_stats.keys():
        min_value = required_stats[stat]
        new_combinations = filter_combinations_by_stat(new_combinations, stat, min_value)
    return new_combinations