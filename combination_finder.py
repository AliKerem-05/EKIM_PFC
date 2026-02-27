import itertools

def find_best_combination(filtered_pool, target_uF, max_parallel=3):
    """
    Elenen havuzdan en fazla 3 paralel parça ile hedefe en yakın büyük değeri bulur.
    """
    best_combo_objs = None
    best_total = float('inf')
    
    for r in range(1, max_parallel + 1):
        for combo in itertools.combinations_with_replacement(filtered_pool, r):
            total = sum(c["cap"] for c in combo)
            # Hedefin üstünde ve şu ana kadarki en küçüğü mü?
            if total >= target_uF and total < best_total:
                best_total = total
                best_combo_objs = combo
                
    if best_combo_objs:
        parts = [c["part"] for c in best_combo_objs]
        caps = [c["cap"] for c in best_combo_objs]
        return parts, caps, best_total
    return None, None, None