import copy
import random
from game import Game, WHITE, BLACK, GRID_COUNT
import ai
import time

NUM_PLAYS = 1000

def score_check():
    print('Checking score:')
    simulator = Game()

    for play_i in range(NUM_PLAYS):
        print("Play {}/{}".format(play_i + 1, NUM_PLAYS))

        simulator.reset(BLACK)

        i = 0

        long_run_simulator = Game()
        long_run_simulator.reset(BLACK, simulator.state()[1])

        long_run_heuristic = ai.Heuristic(long_run_simulator)
        new_heuristic = ai.Heuristic(simulator)

        if new_heuristic.score != long_run_heuristic.score:
            print(new_heuristic.score)
            print(long_run_heuristic.score)
            raise ValueError('Initial heuristics disagree')

        while not simulator.game_over:
            (r, c) = random.choice(simulator.get_actions())
            # (r, c) = simulator.rand_move()

            long_run_heuristic.place(long_run_simulator.state()[0], r, c)
            simulator.place(r, c)

            # Will destroy random rng
            state = simulator.state()
            simulator = Game(*state)

            new_heuristic = ai.Heuristic(simulator)

            if new_heuristic.score != long_run_heuristic.score:
                print(new_heuristic.score)
                print(long_run_heuristic.score)
                #if i == 0:
                #    print('Difference at move 0')
                raise ValueError(f'Heuristic values disagree at move {i}')

            i += 1


    print('Done')

def line_check_new():
    simulator = Game()

    for play_i in range(NUM_PLAYS):
        print("Play {}/{}".format(play_i + 1, NUM_PLAYS))

        simulator.reset(BLACK)
        i = 0

        while not simulator.game_over:
            #(r, c) = random.choice(simulator.get_actions())
            (r, c) = simulator.rand_move()

            simulator.place(r, c)

            # Will destroy random rng
            # state = simulator.state()
            # simulator = Game(*state)

            new_heuristic = ai.Heuristic(simulator)
            new_heuristic.check()
            i += 1

    print('Done')

def line_check_incremental():
    simulator = Game()

    for play_i in range(NUM_PLAYS):
        print("Play {}/{}".format(play_i + 1, NUM_PLAYS))

        simulator.reset(BLACK)
        incremental_heuristic = ai.Heuristic(simulator)

        i = 0

        incremental_heuristic.check()

        while not simulator.game_over:
            (r, c) = random.choice(simulator.get_actions())
            #(r, c) = simulator.rand_move()

            incremental_heuristic.place(simulator.state()[0], r, c)

            # Will destroy random rng
            # state = simulator.state()
            # simulator = Game(*state)

            # print(f'Checking move {i}')
            incremental_heuristic.check()

            # if play_i == 1 and i == 36:
            #     print('Here')
            i += 1

    print('Done')

score_check()