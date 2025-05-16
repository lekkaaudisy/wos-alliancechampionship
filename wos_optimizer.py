import random
import itertools
import copy
from collections import Counter
import math # For probabilistic battle

# --- Game Data (Provided by User) ---
MY_PLAYERS_POOL = [
    1383, 1390, 1401, 1409, 1452, 1454, 1467, 1498, 1625, 1647,
    1780, 1842, 1842, 1862, 1902, 1963, 1999, 2330, 2381, 3761,
    1419, 1465, 1487, 1495, 1517, 1537, 1549, 1578, 1582, 1599,
    1649, 1699, 1718, 1840, 1860, 1921, 1940, 2477, 2808, 2940,
    1292, 1297, 1300, 1301, 1316, 1321, 1324, 1327, 1328, 1331,
    1331, 1339, 1344, 1350, 1352, 1356, 1359, 1359, 1367, 1375
]

ENEMY_TEAM = {
    'left': [
        1361, 1364, 1367, 1368, 1370, 1371, 1373, 1374, 1380, 1386,
        1388, 1393, 1401, 1409, 1423, 1429, 1441, 1442, 1457, 1465
    ],
    'middle': [
        1466, 1469, 1479, 1488, 1572, 1646, 1697, 1732, 1753, 1803,
        1819, 1858, 1884, 2002, 2014, 2060, 2123, 2149, 2545, 3060
    ],
    'right': [
        1468, 1475, 1483, 1497, 1504, 1564, 1624, 1680, 1722, 1737,
        1776, 1818, 1819, 1869, 1908, 2008, 2023, 2297, 2869, 3064
    ],
}

# --- GA and Simulation Parameters ---
# GA Parameters
POPULATION_SIZE = 50
NUM_GENERATIONS = 500 # You might want to increase this for longer runs
CROSSOVER_RATE = 0.8
MUTATION_RATE = 0.2
TOURNAMENT_SIZE = 3
ELITISM_COUNT = 2

# Simulation Parameters
LANE_SIZE = 20
NUM_SIMULATIONS_PER_LANE_BATTLE = 500 # You might want to increase this for longer runs
POWER_DEGRADATION_MIN = 0.05
POWER_DEGRADATION_MAX = 0.15
BATTLE_K_FACTOR = 0.017 # Tune this based on observed game upsets!

# Hybrid Fitness Parameters
UNIVERSAL_LANE_THRESHOLD = 0.60 # P(Win) for a lane to be considered "universal"
BONUS_PER_UNIVERSAL_LANE = 0.5 # Fitness bonus for each universal lane
BONUS_ALL_3_UNIVERSAL = 2.0    # Additional massive bonus if all 3 are universal

lane_battle_cache = {}

# --- 1. Battle Simulation (with Probabilistic 1v1) ---

def determine_1v1_winner_probabilistic(p1_power, p2_power, k_factor=BATTLE_K_FACTOR):
    power_difference = p1_power - p2_power
    prob_p1_wins = 1 / (1 + math.exp(-k_factor * power_difference))
    return random.random() < prob_p1_wins

def simulate_lane_battle_single_run(my_lane_roster, enemy_lane_roster):
    my_players_q = list(my_lane_roster)
    enemy_players_q = list(enemy_lane_roster)
    if not my_players_q: return False
    if not enemy_players_q: return True
    current_my_player_power = float(my_players_q.pop(0))
    current_enemy_player_power = float(enemy_players_q.pop(0))

    while True:
        my_player_wins_1v1 = determine_1v1_winner_probabilistic(
            current_my_player_power, current_enemy_player_power
        )
        if my_player_wins_1v1:
            degradation = random.uniform(POWER_DEGRADATION_MIN, POWER_DEGRADATION_MAX)
            current_my_player_power *= (1 - degradation)
            if not enemy_players_q: return True
            current_enemy_player_power = float(enemy_players_q.pop(0))
        else:
            degradation = random.uniform(POWER_DEGRADATION_MIN, POWER_DEGRADATION_MAX)
            current_enemy_player_power *= (1 - degradation)
            if not my_players_q: return False
            current_my_player_power = float(my_players_q.pop(0))

def get_lane_win_probability(my_lane_sorted, enemy_lane_roster, enemy_lane_key):
    cache_key = (tuple(my_lane_sorted), enemy_lane_key)
    if cache_key in lane_battle_cache:
        return lane_battle_cache[cache_key]
    wins = 0
    for _ in range(NUM_SIMULATIONS_PER_LANE_BATTLE):
        if simulate_lane_battle_single_run(my_lane_sorted, enemy_lane_roster):
            wins += 1
    probability = wins / NUM_SIMULATIONS_PER_LANE_BATTLE
    lane_battle_cache[cache_key] = probability
    return probability

# --- 2. Fitness Evaluation (Hybrid Approach) ---
def calculate_fitness_hybrid(individual_permutation, enemy_team_data):
    # 1. Form and sort player lanes
    my_lanes_as_slots = [
        sorted(individual_permutation[0:LANE_SIZE]),
        sorted(individual_permutation[LANE_SIZE : 2 * LANE_SIZE]),
        sorted(individual_permutation[2 * LANE_SIZE : 3 * LANE_SIZE])
    ]

    enemy_lane_keys = list(enemy_team_data.keys()) # ['left', 'middle', 'right'] or similar

    # 2. Check for "Universal Lanes"
    universal_lane_bonuses = 0
    num_universal_lanes = 0
    
    # Store win probabilities for each of my lanes against each enemy lane to reuse
    # Key: (my_lane_idx, enemy_lane_key), Value: win_prob
    all_nine_matchup_probs = {} 

    for i, my_lane_roster in enumerate(my_lanes_as_slots):
        wins_against_all_enemy_lanes = True
        min_win_prob_for_this_my_lane = 1.0
        for enemy_key in enemy_lane_keys:
            enemy_roster = enemy_team_data[enemy_key]
            prob = get_lane_win_probability(my_lane_roster, enemy_roster, enemy_key)
            all_nine_matchup_probs[(i, enemy_key)] = prob # Store for reuse
            if prob < UNIVERSAL_LANE_THRESHOLD:
                wins_against_all_enemy_lanes = False
            min_win_prob_for_this_my_lane = min(min_win_prob_for_this_my_lane, prob)
        
        if wins_against_all_enemy_lanes: # Or use: if min_win_prob_for_this_my_lane >= UNIVERSAL_LANE_THRESHOLD
            universal_lane_bonuses += BONUS_PER_UNIVERSAL_LANE
            num_universal_lanes += 1

    if num_universal_lanes == 3:
        universal_lane_bonuses += BONUS_ALL_3_UNIVERSAL

    # 3. Calculate Primary Fitness: Min P(Win >= 2/3) across all 6 enemy assignments
    min_prob_win_2_of_3 = 1.0 # Start with max, look for minimum
    
    # Store details for the matchup that gives the min_prob_win_2_of_3,
    # or alternatively, for the one that gives max_prob_win_2_of_3 if min is too pessimistic for display.
    # Let's aim to store details for the MAX P(Win>=2/3) to show the "potential".
    # The GA optimizes based on MIN P(Win>=2/3).
    max_prob_win_2_of_3_for_display = -1.0
    best_matchup_details_for_display = None 
    associated_prob_win_all_3_for_display = -1.0


    for enemy_lane_assignment_perm in itertools.permutations(enemy_lane_keys):
        # enemy_lane_assignment_perm is a tuple like ('left', 'middle', 'right')
        # This means: MySlot0 fights enemy_team[enemy_lane_assignment_perm[0]]
        #             MySlot1 fights enemy_team[enemy_lane_assignment_perm[1]]
        #             MySlot2 fights enemy_team[enemy_lane_assignment_perm[2]]
        
        lane_battle_probs_this_perm = []
        current_perm_match_details = []

        for my_slot_idx in range(3):
            enemy_target_key = enemy_lane_assignment_perm[my_slot_idx]
            # Retrieve pre-calculated probability
            prob_win_slot = all_nine_matchup_probs[(my_slot_idx, enemy_target_key)]
            lane_battle_probs_this_perm.append(prob_win_slot)
            
            # For display details
            current_perm_match_details.append({
                'my_slot_idx': my_slot_idx, 
                'enemy_key': enemy_target_key, 
                'win_prob': prob_win_slot, 
                'my_lane_roster': my_lanes_as_slots[my_slot_idx]
            })

        p = lane_battle_probs_this_perm
        # P(Win >= 2 of 3) for this specific permutation
        current_perm_win_2_of_3_prob = (p[0]*p[1]*(1-p[2])) + \
                                       (p[0]*(1-p[1])*p[2]) + \
                                       ((1-p[0])*p[1]*p[2]) + \
                                       (p[0]*p[1]*p[2])
        
        min_prob_win_2_of_3 = min(min_prob_win_2_of_3, current_perm_win_2_of_3_prob)

        # For display purposes, track the assignment that gave the highest P(Win >= 2/3)
        if current_perm_win_2_of_3_prob > max_prob_win_2_of_3_for_display:
            max_prob_win_2_of_3_for_display = current_perm_win_2_of_3_prob
            best_matchup_details_for_display = current_perm_match_details
            associated_prob_win_all_3_for_display = p[0]*p[1]*p[2]


    # 4. Final Fitness
    # The GA optimizes this total_fitness. Higher is better.
    # primary_fitness_component is the "worst-case" P(Win >= 2/3), ranging 0-1.
    # Bonuses can push this higher.
    total_fitness = min_prob_win_2_of_3 + universal_lane_bonuses

    # Return:
    # 1. total_fitness (for GA optimization)
    # 2. min_prob_win_2_of_3 (the robustness measure)
    # 3. num_universal_lanes (for info)
    # 4. max_prob_win_2_of_3_for_display (for outputting the "potential" of this roster)
    # 5. associated_prob_win_all_3_for_display (for outputting the "potential" of this roster)
    # 6. best_matchup_details_for_display (for outputting the "potential" of this roster)
    return (total_fitness, 
            min_prob_win_2_of_3, 
            num_universal_lanes, 
            max_prob_win_2_of_3_for_display, 
            associated_prob_win_all_3_for_display, 
            best_matchup_details_for_display)


# --- 3. Genetic Algorithm Components (Unchanged from previous 60-player version) ---
def initialize_population(players_pool, pop_size):
    population = []
    for _ in range(pop_size):
        individual = random.sample(players_pool, len(players_pool))
        population.append(individual)
    return population

def tournament_selection(population_with_fitness, tournament_size):
    # population_with_fitness is list of tuples. We sort by element 1 (total_fitness).
    selected_tournament = random.sample(population_with_fitness, tournament_size)
    selected_tournament.sort(key=lambda x: x[1], reverse=True) # x[1] is total_fitness
    return selected_tournament[0][0] # Return the permutation

def order_crossover(parent1_perm, parent2_perm):
    size = len(parent1_perm)
    child_perm = [None] * size
    start, end = sorted(random.sample(range(size), 2))
    child_perm[start:end+1] = parent1_perm[start:end+1]
    segment_values_from_p1 = parent1_perm[start:end+1]
    segment_counts = Counter(segment_values_from_p1)
    p2_available_elements = []
    for val_in_p2 in parent2_perm:
        if segment_counts[val_in_p2] > 0:
            segment_counts[val_in_p2] -= 1 
        else:
            p2_available_elements.append(val_in_p2)
    p2_fill_idx = 0
    for i in range(size):
        if child_perm[i] is None:
            if p2_fill_idx < len(p2_available_elements):
                child_perm[i] = p2_available_elements[p2_fill_idx]
                p2_fill_idx += 1
    if None in child_perm: return list(parent1_perm) 
    return child_perm

def swap_mutation(individual_perm, mutation_rate_per_individual):
    if random.random() < mutation_rate_per_individual:
        size = len(individual_perm)
        idx1, idx2 = random.sample(range(size), 2)
        mutated_perm = list(individual_perm) 
        mutated_perm[idx1], mutated_perm[idx2] = mutated_perm[idx2], mutated_perm[idx1]
        return mutated_perm
    return individual_perm

# --- 4. Main GA Loop (Modified for Hybrid Fitness) ---
def run_genetic_algorithm(players_pool, enemy_team_data):
    global lane_battle_cache 

    population = initialize_population(players_pool, POPULATION_SIZE)
    
    best_overall_individual_perm = None
    best_overall_total_fitness = -float('inf') # GA optimizes this
    
    # Store these details from the individual that had the best_overall_total_fitness
    best_overall_min_P_win_ge2 = -1.0 
    best_overall_num_universal = -1
    best_overall_max_P_win_ge2_display = -1.0
    best_overall_P_win_all_3_display = -1.0
    best_overall_matchup_details_display = None


    for generation in range(NUM_GENERATIONS):
        lane_battle_cache.clear() 

        # List of: (permutation, total_fitness, min_P(Win>=2/3), num_universal, max_P(Win>=2/3)_disp, P(WinAll3)_disp, details_disp)
        population_with_fitness = [] 
        for ind_perm in population:
            fitness_results = calculate_fitness_hybrid(ind_perm, enemy_team_data)
            population_with_fitness.append( (ind_perm, *fitness_results) )

        # Sort population by total_fitness (element at index 1)
        population_with_fitness.sort(key=lambda x: x[1], reverse=True)
        
        current_gen_best_perm = population_with_fitness[0][0]
        current_gen_total_fitness = population_with_fitness[0][1]
        # Extract other metrics for the current generation's best
        current_gen_min_P_win_ge2 = population_with_fitness[0][2]
        current_gen_num_universal = population_with_fitness[0][3]
        current_gen_max_P_win_ge2_disp = population_with_fitness[0][4]
        current_gen_P_win_all_3_disp = population_with_fitness[0][5]
        # current_gen_matchup_details_disp = population_with_fitness[0][6]


        if current_gen_total_fitness > best_overall_total_fitness:
            best_overall_total_fitness = current_gen_total_fitness
            best_overall_individual_perm = current_gen_best_perm
            best_overall_min_P_win_ge2 = current_gen_min_P_win_ge2
            best_overall_num_universal = current_gen_num_universal
            best_overall_max_P_win_ge2_display = current_gen_max_P_win_ge2_disp
            best_overall_P_win_all_3_display = current_gen_P_win_all_3_disp
            best_overall_matchup_details_display = population_with_fitness[0][6] # Store full details
            
        avg_total_fitness = sum(f[1] for f in population_with_fitness) / POPULATION_SIZE
        print(f"Gen {generation + 1}/{NUM_GENERATIONS}: "
              f"Best TotalFit={current_gen_total_fitness:.4f} "
              f"(MinP(W>=2)={current_gen_min_P_win_ge2:.3f}, UnivLanes={current_gen_num_universal}, MaxP(W>=2)={current_gen_max_P_win_ge2_disp:.3f}) "
              f"Avg TotalFit={avg_total_fitness:.4f}, Cache={len(lane_battle_cache)}")


        next_generation_perms = []
        for i in range(ELITISM_COUNT):
            next_generation_perms.append(list(population_with_fitness[i][0]))

        while len(next_generation_perms) < POPULATION_SIZE:
            parent1_perm = tournament_selection(population_with_fitness, TOURNAMENT_SIZE)
            parent2_perm = tournament_selection(population_with_fitness, TOURNAMENT_SIZE)
            
            offspring_perm = parent1_perm 
            if random.random() < CROSSOVER_RATE:
                offspring_perm = order_crossover(parent1_perm, parent2_perm)
            
            offspring_perm = swap_mutation(offspring_perm, MUTATION_RATE)
            
            if None in offspring_perm or len(offspring_perm) != len(players_pool):
                next_generation_perms.append(list(parent1_perm)) 
            else:
                next_generation_perms.append(offspring_perm)
            
        population = next_generation_perms

    return (best_overall_individual_perm, best_overall_total_fitness, 
            best_overall_min_P_win_ge2, best_overall_num_universal,
            best_overall_max_P_win_ge2_display, best_overall_P_win_all_3_display,
            best_overall_matchup_details_display)

# --- 5. Run and Output (Modified for Hybrid Fitness Output) ---
if __name__ == '__main__':
    if len(MY_PLAYERS_POOL) != 3 * LANE_SIZE: raise ValueError("Player pool size error.")
    for key, lane in ENEMY_TEAM.items():
        if len(lane) != LANE_SIZE: raise ValueError(f"Enemy lane '{key}' size error.")

    print("Starting Genetic Algorithm Optimization (Hybrid Robustness Approach)...")
    print(f"Primary Goal: Maximize (WorstCaseP(Win>=2/3) + UniversalLaneBonuses)")
    print(f"Sims per Lane Battle: {NUM_SIMULATIONS_PER_LANE_BATTLE}, K-Factor for upsets: {BATTLE_K_FACTOR}")
    print(f"Universal Lane: P(Win) >= {UNIVERSAL_LANE_THRESHOLD} against ALL enemy lanes.")
    print(f"Bonuses: PerUniversal={BONUS_PER_UNIVERSAL_LANE}, All3Universal={BONUS_ALL_3_UNIVERSAL}")
    print(f"GA Params: Pop={POPULATION_SIZE}, Gens={NUM_GENERATIONS}, CrossRate={CROSSOVER_RATE}, MutRate={MUTATION_RATE}")
    print("-" * 30)

    # For actual long runs, consider removing or setting seed based on needs
    # random.seed(42) 

    results = run_genetic_algorithm(MY_PLAYERS_POOL, ENEMY_TEAM)
    (best_perm, total_fit, min_p_ge2, num_univ, 
     max_p_ge2_disp, p_all3_disp, matchup_disp) = results

    print("\n" + "=" * 30)
    print("Optimization Finished!")
    print("=" * 30)
    
    if best_perm:
        print(f"\nBest Overall Total Fitness (GA Optimized Value): {total_fit:.4f}")
        print(f"  Robustness Score (Min P(Win >= 2 lanes) vs any enemy setup): {min_p_ge2:.4f}")
        print(f"  Number of 'Universal' Lanes found: {num_univ}")
        print(f"\nDetails for the 'Potential Best Matchup' with this roster:")
        print(f"  Max P(Win >= 2 lanes) for this roster (vs optimal enemy assignment): {max_p_ge2_disp:.4f}")
        print(f"  Associated P(Win ALL 3 lanes): {p_all3_disp:.4f}")
        
        print("\nOptimized Lane Distribution (players sorted ascending):")
        my_lane1_opt = sorted(best_perm[0:LANE_SIZE])
        my_lane2_opt = sorted(best_perm[LANE_SIZE : 2 * LANE_SIZE])
        my_lane3_opt = sorted(best_perm[2 * LANE_SIZE : 3 * LANE_SIZE])
        
        optimized_lanes_map_disp = { 0: my_lane1_opt, 1: my_lane2_opt, 2: my_lane3_opt }

        print("\n'Potential Best Matchup' Details (this assignment yielded Max P(Win >= 2/3)):")
        if matchup_disp:
            for detail in matchup_disp:
                my_slot_idx = detail['my_slot_idx']
                enemy_key = detail['enemy_key']
                win_prob = detail['win_prob']
                # Use the consistently derived roster for display
                my_roster_for_slot_disp = optimized_lanes_map_disp[my_slot_idx] 
                
                print(f"  My Players (Slot {my_slot_idx+1}) vs Enemy Lane '{enemy_key}':")
                print(f"    My Roster: {my_roster_for_slot_disp}")
                print(f"    Enemy Roster: {ENEMY_TEAM[enemy_key]}")
                print(f"    P(win this lane battle) = {win_prob:.4f}")
        else:
            print("No matchup details available for display.")
    else:
        print("No solution found.")
