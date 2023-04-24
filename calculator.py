import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
from tqdm import tqdm


def get_optimal_chunk_size(num_simulations):
    num_workers = os.cpu_count()
    chunk_size = int(math.ceil(num_simulations / num_workers))
    print(chunk_size)
    return chunk_size


def worker_simulation(hand_cards, community_cards, num_opponents, num_simulations):
    win_probabilities = []
    for i in range(num_opponents):
        win_probability = estimate_hole_card_win_rate(
            nb_simulation=num_simulations,
            nb_player=num_opponents + 1,
            hole_card=hand_cards,
            community_card=community_cards
        )
        win_probabilities.append(win_probability)
    return win_probabilities


def simulate(hand, board, num_opponents, num_simulations, num_workers=os.cpu_count(), chunk_size=None):
    hand_cards = gen_cards(hand)
    community_cards = gen_cards(board)

    if chunk_size is None:
        chunk_size = get_optimal_chunk_size(num_simulations)

    total_chunks = (num_simulations + chunk_size - 1) // chunk_size
    args = [(hand_cards, community_cards, num_opponents, chunk_size) for _ in range(total_chunks * num_workers)]

    progress_bar = tqdm(total=total_chunks * num_workers, desc="Simulating")

    def update_progress(future):
        progress_bar.update(1)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_simulation, *arg) for arg in args]
        for future in as_completed(futures):
            future.add_done_callback(update_progress)
        results = [future.result() for future in futures]

    progress_bar.close()

    win_probabilities = [0.0] * num_opponents
    for opponent_results in results:
        for i in range(num_opponents):
            win_probabilities[i] += opponent_results[i]

    win_probabilities = [win_probability / (total_chunks * num_workers) for win_probability in win_probabilities]

    for i, win_probability in enumerate(win_probabilities[:-1]):
        print(f"Opponent {i + 1} win probability: {win_probability * 100:.2f}%")

    return win_probabilities[-1]


def main():
    hand_input = input("Enter your two cards (e.g., 'SA DA'): ")
    hand_cards = hand_input.split()

    board_input = input("Enter the community cards (e.g., 'S7 D8 S9') or leave blank if none: ")
    board_cards = board_input.split() if board_input else []

    num_opponents = int(input("Enter the number of opponents: "))
    num_simulations = int(input("Enter the number of simulations: "))

    win_probability = simulate(hand_cards, board_cards, num_opponents, num_simulations)
    print(f"Win probability: {win_probability * 100:.2f}%")


if __name__ == "__main__":
    main()
