# Whiteout Survival - Alliance Championship Lane Optimizer (WOS Optimizer)

This project uses a Genetic Algorithm (GA) to help you find optimal lane assignments for your team in the **Whiteout Survival Alliance Championship** event. The goal is to maximize your chances of winning at least 2 out of 3 lane battles against a known enemy team lineup. This optimizer encourages robust strategies by also rewarding "universal" lanes that can perform well against multiple enemy lane configurations.

The core of the optimizer is a battle simulation that models:
*   Sequential 1v1 fights within each lane.
*   Probabilistic outcomes for each 1v1 fight based on Player Power, allowing for upsets.
*   Power degradation for 1v1 winners.

## Features

*   **Genetic Algorithm Optimization:** Distributes your specified Player Power values into 3 optimal lanes.
*   **Hybrid Robustness Fitness Function:**
    *   **Primary Goal:** Maximizes your *worst-case* probability of winning at least 2 out of 3 lanes (considers all 6 ways your lanes can match against the enemy's). This helps counter enemy lane switching.
    *   **Secondary Goal:** Rewards solutions that develop "universal lanes" – lanes with a high win probability against *all three* of the enemy's specific lanes.
*   **Probabilistic Battle Simulation for Whiteout Survival:**
    *   Each 1v1 Player-vs-Player fight is determined probabilistically using player Player Power values and a configurable K-Factor. This simulates the inherent randomness and potential for upsets in Whiteout Survival battles.
    *   Winners of 1v1 fights experience a random power degradation (default 5%-15%) before facing the next opponent Player.
*   **Configurable Parameters:** Fine-tune GA settings, the number of simulations, the K-Factor for battle upsets, criteria for universal lanes, and their associated fitness bonuses.
*   **Detailed Output:** Provides GA progress and a summary of the best Player Power distribution, its calculated robustness score, number of universal lanes found, and details for its potential best-case matchup.

## Game Setup (Assumed by the Optimizer for Alliance Championship)

*   **3 Lanes per Side.**
*   **20 Playeres (Players/Participants) per Lane per Side.**
*   Your Alliance provides 60 Player Power values; the enemy Alliance's 60 Player Power values are also known.
*   Enemy lane assignments and Player Power order (sorted ascending by power) are **fixed and known for the current planning phase**.
*   Your Playeres can be freely distributed by the optimizer into 3 lanes of 20.
*   Your formed lanes are **sorted ascending by Player Power** before battle simulation.
*   Battles are lane vs. lane, with sequential 1v1 Player fights starting from the weakest Player Power.

## How it Works

1.  **Individual Representation:** A candidate solution in the GA is an arrangement of your 60 Player Power values, which is then split into three 20-Player lanes.
2.  **Fitness Evaluation:**
    *   Each of your formed lanes (sorted by Player Power) is evaluated.
    *   **Universality Check:** Each of your lanes is simulated against all three enemy lanes. If a lane meets a defined win probability threshold (e.g., >60%) against *all* enemy lanes, it's considered "universal," and a bonus is added to the solution's fitness.
    *   **Robustness Score:** The optimizer considers all 6 ways your three lanes can be matched against the enemy's three lanes. For each matchup, it calculates the probability of winning at least 2 out of 3 lanes (P(Win >= 2/3)). The *minimum* of these 6 probabilities is the primary robustness component of the fitness.
    *   **Total Fitness:** The GA aims to maximize `Total Fitness = Robustness Score + Universal Lane Bonuses`.
3.  **Battle Simulation:**
    *   Each lane-vs-lane battle is simulated hundreds of times (e.g., `NUM_SIMULATIONS_PER_LANE_BATTLE = 500`) for an accurate win probability.
    *   The outcome of a 1v1 Player fight uses a logistic function based on Player Power differences and a tunable `BATTLE_K_FACTOR` to allow for realistic upsets.
4.  **Genetic Algorithm:** Uses standard operators (Tournament Selection, Order Crossover, Swap Mutation, Elitism) to evolve solutions over generations.

## Requirements

*   Python 3.x
*   Standard Python libraries: `random`, `itertools`, `copy`, `collections`, `math`.

## Setup and Usage

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/lekkaaudisy/wos-alliancechampionship.git
    cd wos-alliancechampionship
    ```
2.  **Configure Data and Parameters (in the Python script, e.g., `wos_optimizer.py`):**
    *   **`MY_PLAYERS_POOL`**: Update this list with your Alliance's 60 Player Power values.
    *   **`ENEMY_TEAM`**: Update this dictionary with the opponent Alliance's 3 fixed lanes (each a list of 20 Player Power values, sorted ascending).
    *   **`LANE_SIZE`**: Ensure this matches the number of Playeres per lane in your Alliance Championship (default is 20).
    *   **`BATTLE_K_FACTOR` (CRITICAL!)**: This value dictates upset likelihood in 1v1 Player fights. **You MUST tune this!**
        *   *How to Tune:* Observe real AC battles or duels. If a Player with X power less than its opponent wins Y% of the time, adjust `BATTLE_K_FACTOR` until simple test simulations (using the `determine_1v1_winner_probabilistic` function) replicate similar upset frequencies. A starting range for tuning might be `0.01` to `0.03`. A `BATTLE_K_FACTOR` of `0.017` means a 100 power difference gives the stronger side ~85% win chance for that 1v1.
    *   **`NUM_SIMULATIONS_PER_LANE_BATTLE`**: Higher values (e.g., 500) give more accurate win probabilities but take longer. If time is an issue, 100-200 can be a faster starting point for initial tests.
    *   **Hybrid Fitness Parameters (`UNIVERSAL_LANE_THRESHOLD`, `BONUS_PER_UNIVERSAL_LANE`, etc.)**: Adjust these to control how much the GA prioritizes finding "universal" lanes.
    *   GA parameters (`POPULATION_SIZE`, `NUM_GENERATIONS`, etc.).
3.  **Run the optimizer:**
    ```bash
    python wos_optimizer.py 
    ```
    (Replace `wos_optimizer.py` with the actual name of your script).
4.  **Patience is Key:** The optimization, especially with many simulations, can take a significant amount of time (minutes to hours).

## Interpreting the Output

*   **Per-Generation Log:** Shows the progress of the GA, including:
    *   `Best TotalFit`: The fitness score the GA is maximizing.
    *   `MinP(W>=2)`: The robustness of the best solution (its worst-case P(Win >= 2/3)).
    *   `UnivLanes`: Number of "universal" lanes in the best solution.
    *   `MaxP(W>=2)`: The best-case P(Win >= 2/3) for that solution.
*   **Final Output:**
    *   A summary of the best overall Player Power distribution found.
    *   The specific Player Powers assigned to each of your three lanes (sorted ascending).
    *   Details of the "Potential Best Matchup" this optimized roster could achieve if the enemy lanes align favorably for you.

## Disclaimer: Important Considerations & Limitations

This Whiteout Survival Alliance Championship Lane Optimizer is a powerful strategic planning tool, but it's essential to understand its capabilities and limitations:

1.  **Model, Not a Crystal Ball:** The optimizer provides recommendations based on a mathematical model and simulations of game mechanics as understood and implemented. Whiteout Survival is a complex game with many interacting systems. This tool **cannot perfectly predict the outcome of every battle or guarantee wins.**
2.  **"Power" as an Abstraction:** The optimizer primarily uses "Player Power" as the input for each participant. While Player Power is a significant indicator, it doesn't capture the full nuance of:
    *   **Specific Hero Compositions and Synergies:** The unique abilities, skill procs, and interactions between specific heroes are not explicitly modeled beyond their contribution to overall Player Power and the general probabilistic combat.
    *   **Troop Type Advantages/Counters:** While the probabilistic model (via the `BATTLE_K_FACTOR`) attempts to implicitly account for some level of upset potential that might arise from counters, it does not simulate specific Infantry-Marksman-Lancer counter mechanics in detail.
    *   **Hero Gear, Chief Gear and Charm, Research, Pet, Additional Buff:** These factors contribute to Player Power but their specific, granular effects on skill damage, proc rates, or survivability beyond that aggregate power are not individually simulated.
    *   **Formation and Targeting AI:** The optimizer assumes a standard sequential battle. Specific in-game formations or hero skill targeting priorities are not part of this simulation.
3.  **The `BATTLE_K_FACTOR` is Crucial and Subjective:** The accuracy of the probabilistic 1v1 battle outcomes heavily relies on the `BATTLE_K_FACTOR`.
    *   This factor needs to be **tuned by you** based on your observations of real game battles and upset frequencies.
    *   An incorrectly tuned `BATTLE_K_FACTOR` can lead the optimizer to favor strategies that are either too risky or too conservative for the actual level of randomness in Whiteout Survival.
4.  **Randomness (RNG):** Whiteout Survival, like many games, involves significant Random Number Generation (RNG) in skill activations, critical hits, and other combat events.
    *   The optimizer uses simulations to average out this randomness and estimate probabilities.
    *   However, in any single real battle, RNG can lead to outcomes that deviate significantly from the simulated average. A 90% chance to win still means a 10% chance to lose.
5.  **Fixed Enemy Assumption:** The optimizer assumes you have a fixed, known enemy lane setup for the planning phase. If the enemy changes their lanes unpredictably *after* you've set yours based on this tool, the "robustness" score (Min P(Win >= 2/3)) attempts to account for this, but specific matchups will change.
6.  **Dynamic Game Environment:** Whiteout Survival is subject to updates, balance changes, new heroes, and new mechanics. This optimizer is based on the game mechanics understood at the time of its development/last update. Significant game changes might require adjustments to the simulation logic or parameters.
7.  **Use as a Strategic Aid:** This tool is best used as an aid to your strategic decision-making, not as an absolute directive. Combine its recommendations with:
    *   Your deep knowledge of Whiteout Survival mechanics.
    *   Your understanding of your Alliance members' strengths and weaknesses beyond just Player Power.
    *   Your assessment of the current meta and typical enemy strategies.
    *   Common sense and strategic judgment.

**By using this tool, you acknowledge that it provides theoretical optimizations based on a simplified model of the game, and actual results may vary. Always exercise your own judgment and adapt your strategies as needed.**

## Future Enhancements

*   **External Configuration:** Move all settings and data to JSON/YAML files.
*   **More Detailed Simulation:** If data on specific hero/troop counters or skill impacts becomes available and can be modeled efficiently, the simulation could be enhanced.
*   **GUI for easier input/output.**

## Contributing

Contributions are welcome and appreciated! Whether it's reporting a bug, suggesting an enhancement, improving documentation, or submitting code changes, your help can make this optimizer better for the Whiteout Survival community.

Please consider the following guidelines:

**1. Reporting Bugs or Issues:**

*   Before submitting a new issue, please check the existing [Issues](https://github.com/lekkaaudisy/wos-alliancechampionship/issues) to see if your problem has already been reported.
*   If you find a new bug, please provide as much detail as possible:
    *   Steps to reproduce the bug.
    *   Expected behavior.
    *   Actual behavior.
    *   Your Python version and any relevant environment details.
    *   Screenshots or logs if applicable.
    *   The specific input data (`MY_PLAYERS_POOL`, `ENEMY_TEAM`) and parameters (`BATTLE_K_FACTOR`, etc.) you were using.

**2. Suggesting Enhancements or New Features:**

*   We're open to ideas! If you have a suggestion for a new feature or an improvement to an existing one, please create an [Issue](https://github.com/lekkaaudisy/wos-alliancechampionship/issues).
*   Describe the feature clearly and explain why you think it would be valuable.
*   If you're willing to implement it yourself, that's even better!

**Areas where contributions would be particularly helpful:**

*   Implementing an external configuration file (e.g., JSON/YAML) for data and parameters.
*   Refining the `BATTLE_K_FACTOR` based on extensive game observation or data.
*   Adding more sophisticated simulation details (if they can be modeled efficiently).
*   Developing a simple GUI for easier input and visualization of results.
*   Performance optimizations.

Thank you for considering contributing to the Whiteout Survival Alliance Championship Optimizer!
