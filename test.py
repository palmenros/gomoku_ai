# NOTE: do not modify this file
import random
from game import Game, WHITE, BLACK, GRID_COUNT
import ai
import stock_ai
import time

TOL = 0.01

def load_UCB_arr(text):
    action_win_UCB_sol = {}
    for line in text.split("\n"):
        tokens = line.strip().split(" ")
        action_win_UCB_sol[(int(tokens[0]), int(tokens[1]))] = float(tokens[2])
    return action_win_UCB_sol


def deterministic_test():
    sols = []
    states = []

    with open("test_sols") as file:
        text = file.read()

        sols_text = text.split("\n\n")[:-1]
        
        for sol_text in sols_text:
            sols.append(load_UCB_arr(sol_text))
            
    with open("test_states") as file:
        states = file.readlines()

    states = [state[:-1] for state in states]

    assert(len(states) == len(sols))
    num_tests = len(states)
    test_num = 1
    for state, sol in zip(states, sols):
        print("test {}/{}".format(test_num, num_tests))
        game = Game()
        game.load_state_text(state)

        ai_player = AI(game.state())
        _, UCBs = ai_player.mcts_search()

        incorrect_cnt = 0
        for key in sol:
            if (UCBs[key] - sol[key] <= TOL and 
                UCBs[key] - sol[key] >= -TOL):
                pass
            else:
                print("Incorrect UCB for action:", key)
                print("yours/correct: {}/{}".format(UCBs[key], sol[key]))
                incorrect_cnt += 1

        print()
        if incorrect_cnt == 0:
            print("PASSED")
        else:
            print("FAILED")
        print()

        test_num += 1

#MIN_WINS = 9
NUM_PLAYS = 100

def win_test():
    simulator = Game()
    wins = 0

    sum_time_new = 0
    sum_time_old = 0
    num_moves_new = 0
    num_moves_old = 0
    max_time_new = -10000
    max_time_old = -10000
    started_by_new_ai = 0

    for play_i in range(NUM_PLAYS):
        print("play {}/{}".format(play_i + 1, NUM_PLAYS))
        simulator.reset(BLACK)

        ai_play = bool(random.getrandbits(1))
        if ai_play:
            new_ai_color = BLACK
            print('New AI starts the game')
            started_by_new_ai += 1
        else:
            new_ai_color = WHITE
            print('Stock AI starts the game')

        move_index = 0
        while not simulator.game_over:
            #print(f'Move {move_index}')
            if ai_play:
                start_time = time.time()
                ai_player = ai.AI(simulator.state())
                (r,c), _ = ai_player.mcts_search()
                move_time = time.time() - start_time
                sum_time_new += move_time
                num_moves_new += 1
                max_time_new = max(max_time_new, move_time)
            else:
                start_time = time.time()
                ai_player = stock_ai.AI(simulator.state())
                (r,c), _ = ai_player.mcts_search()
                move_time = time.time() - start_time
                sum_time_old += move_time
                num_moves_old += 1
                max_time_old = max(max_time_old, move_time)
                #(r,c) = simulator.rand_move()

            simulator.place(r, c)
            ai_play = not ai_play
            move_index += 1

        if simulator.winner == new_ai_color:
            print("New AI won.")
            wins += 1
        else:
            print("Stock AI won.")

    print(f'Average move time new: {sum_time_new / num_moves_new} seconds')
    print(f'Max move time new: {max_time_new} seconds')

    print(f'Average move time old: {sum_time_old / num_moves_old} seconds')
    print(f'Max move time old: {max_time_old} seconds')


    print(f'New AI won {round(100 * wins / NUM_PLAYS, 2)}% of matches ({wins} out of {NUM_PLAYS})')
    print(f'New AI started {round(100 * started_by_new_ai / NUM_PLAYS, 2)}% of matches ({started_by_new_ai} out of {NUM_PLAYS})')