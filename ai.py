from __future__ import absolute_import, division, print_function

import math
from math import sqrt, log
from game import Game, WHITE, BLACK, GRID_COUNT, EMPTY
import copy
import time
import random

class Node:
    # NOTE: modifying this block is not recommended
    def __init__(self, state, actions, parent=None):
        self.state = (state[0], copy.deepcopy(state[1]))
        self.num_wins = 0 #number of wins at the node
        self.num_visits = 0 #number of visits of the node
        self.parent = parent #parent node of the current node
        self.children = [] #store actions and children nodes in the tree as (action, node) tuples
        self.simulator = Game(*state)
        self.is_terminal = self.simulator.game_over
        self.heuristic = Heuristic(self.simulator)
        self.untried_actions = self.get_possible_actions(copy.deepcopy(actions)) #store actions that have not been tried

    def get_possible_actions(self, actions):
        color = self.state[0]

        # Check for forced wins
        for dir in DIRS:
            for line in self.heuristic.lines[dir][color]:
                if line.num_consecutive == 4:
                    return [line.get_open_ends()[0]]

        # TODO: Only return forced wins / forced defenses
        forced_defenses = []
        for dir in DIRS:
            for line in self.heuristic.lines[dir][other_color(color)]:
                if line.num_consecutive == 4:
                    forced_defenses += line.get_open_ends()

        if len(forced_defenses) > 0:
            return forced_defenses

        return actions

# NOTE: deterministic_test() requires BUDGET = 1000
# You can try higher or lower values to see how the AI's strength changes
BUDGET = 1000

#[(0, 0), (0, 1), ..., (0, GRID_COUNT-1)]
STARTING_HOR = set(((0, i) for i in range(GRID_COUNT)))

#[(0, 0), (1, 0), ..., (GRID_COUNT-1, 0)]
STARTING_VER = set((i, 0) for i in range(GRID_COUNT))

STARTING_DIAG_DOWN_RIGHT = STARTING_HOR.union(STARTING_VER)

STARTING_DIAG_UP_RIGHT = STARTING_HOR.union(set((i, GRID_COUNT-1) for i in range(GRID_COUNT)))

DIR_HOR = 0
DIR_VER = 1
DIR_DIAG_DOWN_RIGHT = 2
DIR_DIAG_UP_RIGHT = 3

DIRS = [DIR_HOR, DIR_VER, DIR_DIAG_DOWN_RIGHT, DIR_DIAG_UP_RIGHT]
COLORS = [BLACK, WHITE]

DIR_TO_DELTA = {
    DIR_HOR: (1, 0),
    DIR_VER: (0, 1),
    DIR_DIAG_DOWN_RIGHT: (1, 1),
    DIR_DIAG_UP_RIGHT: (1, -1)
}

DIR_TO_STARTING = {
    DIR_HOR: STARTING_HOR,
    DIR_VER: STARTING_VER,
    DIR_DIAG_DOWN_RIGHT: STARTING_DIAG_DOWN_RIGHT,
    DIR_DIAG_UP_RIGHT: STARTING_DIAG_UP_RIGHT
}

class ConsecutiveLine:
    def __init__(self, start, end, start_open_end, end_open_end, dir, color, num_consecutive):
        self.start = start
        self.end = end
        self.start_open_end = start_open_end
        self.end_open_end = end_open_end
        self.dir = dir
        self.color = color
        self.cached_score = math.inf

        self.num_consecutive = num_consecutive
        self.num_open_ends = len(self.get_open_ends())

    def check(self, grid):
        dx, dy = DIR_TO_DELTA[self.dir]
        x, y = self.start

        if self.num_open_ends == 0 and self.num_consecutive < 5:
            raise ValueError("We shouldn't store consecutive useless lines without open ends")

        for i in range(self.num_consecutive):
            if grid[x][y] != self.color:
                raise ValueError('Incorrect Consecutive Line')
            x += dx
            y += dy

        if (x-dx, y-dy) != self.end:
            raise ValueError('Incorrect end')

        def is_within_bounds(x, y):
            return 0 <= x < GRID_COUNT and 0 <= y < GRID_COUNT

        def safe_is_empty(x, y):
            return is_within_bounds(x, y) and grid[x][y] == EMPTY

        def safe_check(x, y, col):
            return is_within_bounds(x, y) and grid[x][y] == col

        num_open_ends = 0

        if self.start_open_end:
            num_open_ends += 1
            if not safe_is_empty(self.start[0]-dx, self.start[1] - dy):
                raise ValueError('Incorrect Consecutive Line (Start end not EMPTY)')
        else:
            if safe_check(self.start[0]-dx, self.start[1]-dy, self.color):
                raise ValueError('Incorrect Consecutive Line (Start end this line color)')

        if self.end_open_end:
            num_open_ends += 1

            if not safe_is_empty(self.end[0] + dx, self.end[1] + dy):
                raise ValueError('Incorrect Consecutive Line (End not EMPTY)')
        else:
            if safe_check(self.end[0] + dx, self.end[1] + dy, self.color):
                raise ValueError('Incorrect Consecutive Line (End this line color)')

        if num_open_ends != self.num_open_ends:
            raise ValueError('Incorrect stored value of num_open_ends')

    def get_open_ends(self):
        dx, dy = DIR_TO_DELTA[self.dir]
        res = []
        if self.start_open_end:
            res.append((self.start[0] - dx, self.start[1] - dy))

        if self.end_open_end:
            res.append((self.end[0] + dx, self.end[1] + dy))

        return res

    def is_starting_end(self, x, y):
        dx, dy = DIR_TO_DELTA[self.dir]
        return self.start_open_end and (self.start[0] - dx, self.start[1] - dy) == (x, y)

    def _calc_score(self, current_turn):
        if self.num_consecutive > 4:
            return 200000000
        elif self.num_consecutive == 4:
            if self.num_open_ends == 1:
                if current_turn:
                    return 100000000
                return 50
            elif self.num_open_ends == 2:
                if current_turn:
                    return 100000000
                return 500000
        elif self.num_consecutive == 3:
            if self.num_open_ends == 1:
                if current_turn:
                    return 7
                return 5
            elif self.num_open_ends == 2:
                if current_turn:
                    return 10000
                return 50
        elif self.num_consecutive == 2:
            if self.num_open_ends == 1:
                return 2
            else:
                return 5
        elif self.num_consecutive == 1:
            if self.num_open_ends == 1:
                return 0.5
            else:
                return 1
        raise ValueError('We should never reach this')

    def score(self, this_turn_color):
        if self.num_open_ends == 0 and self.num_consecutive < 5:
            raise ValueError("We shouldn't store consecutive useless lines without open ends")

        current_turn = self.color == this_turn_color

        self.cached_score = self._calc_score(current_turn)
        return self.cached_score

    def get_open_start(self):
        dx, dy = DIR_TO_DELTA[self.dir]

        if not self.start_open_end:
            ValueError('There is no open start')
        return self.start[0] - dx, self.start[1] - dy

    def get_open_end(self):
        dx, dy = DIR_TO_DELTA[self.dir]

        if not self.end_open_end:
            ValueError('There is no open end')
        return self.start[0] + dx, self.start[1] + dy


def other_color(color):
    if color == BLACK:
        return WHITE
    return BLACK


class Heuristic:
    def __init__(self, simulator):
        self.simulator = simulator
        self.score = {BLACK: 0, WHITE: 0}
        self.lines = {}
        self.open_end_dicts = {}
        self.reset()

    def reset(self):
        # Construct list of consecutive stones of a color and open ends
        for dir in DIRS:
            self.lines[dir] = {}
            self.open_end_dicts[dir] = {}
            for color in COLORS:
                discovered_lines, open_ends_dict = self.find_consecutive_dir(color, dir)
                self.lines[dir][color] = discovered_lines
                self.open_end_dicts[dir][color] = open_ends_dict

    def find_consecutive_dir(self, color, dir):

        starting = DIR_TO_STARTING[dir]
        dx, dy = DIR_TO_DELTA[dir]

        grid = self.simulator.state()[1]
        count_consecutive = 0

        discovered_lines = []
        open_ends_dict = {}

        starting_open_end = False
        start_coords = None
        end_coords = None

        def add_line(is_ending_open_end):
            # Do not record, this is a dead line, won't ever be useful
            if count_consecutive < 5 and not starting_open_end and not is_ending_open_end:
                return

            line = ConsecutiveLine(start_coords, end_coords, starting_open_end, is_ending_open_end, dir, color, count_consecutive)
            discovered_lines.append(line)

            # Add open ends to open end map
            open_ends = line.get_open_ends()
            for open_end in open_ends:
                if open_end not in open_ends_dict:
                    open_ends_dict[open_end] = [line]
                else:
                    open_ends_dict[open_end].append(line)

            # Add score
            self.score[color] += line.score(self.simulator.state()[0])

        def is_within_bounds(x, y):
            return 0 <= x < GRID_COUNT and 0 <= y < GRID_COUNT

        for sx, sy in starting:
            x, y = sx, sy

            while is_within_bounds(x, y):
                # Do a linear pass starting at sx, sy and incrementing by dx, dy
                if grid[x][y] == color:
                    if count_consecutive == 0:
                        start_coords = (x, y)
                    count_consecutive += 1
                elif grid[x][y] == EMPTY and count_consecutive > 0:
                    end_coords = (x-dx, y-dy)
                    add_line(True)
                    count_consecutive = 0

                    starting_open_end = True
                elif grid[x][y] == EMPTY:
                    starting_open_end = True
                elif count_consecutive > 0:
                    end_coords = (x-dx, y-dy)
                    add_line(False)
                    count_consecutive = 0
                    starting_open_end = False
                else:
                    starting_open_end = False
                x += dx
                y += dy

            if count_consecutive > 0:
                end_coords = (x - dx, y - dy)
                add_line(False)

            count_consecutive = 0
            starting_open_end = False

        return discovered_lines, open_ends_dict

    def place(self, new_color, x, y):
        self.simulator.place(x, y)
        grid = self.simulator.state()[1]

        def is_within_bounds(x, y):
            return 0 <= x < GRID_COUNT and 0 <= y < GRID_COUNT

        def safe_is_empty(x, y):
            return is_within_bounds(x, y) and grid[x][y] == EMPTY

        def safe_is_color(x, y, col):
            return is_within_bounds(x, y) and grid[x][y] == col

        # Handle first the same that we are placing
        for dir in DIRS:
            open_dict = self.open_end_dicts[dir][new_color]
            dx, dy = DIR_TO_DELTA[dir]
            if (x, y) in open_dict:
                # The point we are updating is already an end
                lines = open_dict[(x, y)]

                if len(lines) == 1:
                    # Only open end of one part, no need to merge
                    line = lines[0]

                    open_dict[(x, y)] = []

                    line.num_consecutive += 1
                    if line.is_starting_end(x, y):
                        line.start = (x, y)
                        if safe_is_empty(x-dx, y-dy):
                            open_dict[(x-dx, y-dy)] = [line]
                        else:
                            line.start_open_end = False
                            line.num_open_ends -= 1

                            if safe_is_color(x-dx, y-dy, new_color):
                                raise ValueError("len(lines)=1, this shouldn't happen")

                    else:
                        line.end = (x, y)
                        if safe_is_empty(x+dx, y+dy):
                            open_dict[(x + dx, y + dy)] = [line]
                        else:
                            line.start_open_end = False
                            line.num_open_ends -= 1

                            if safe_is_color(x + dx, y + dy, new_color):
                                raise ValueError("len(lines)=1, this shouldn't happen")

                else:
                    # Open end to two different lines, we need to merge them

                    # We find the minimum depending on the direction we're looking at and put in minimum, put the
                    # other on maximum
                    minimum : ConsecutiveLine = lines[0]
                    maximum : ConsecutiveLine = lines[1]

                    order_index = 0
                    if dir == DIR_VER:
                        order_index = 1

                    if maximum.start[order_index] < minimum.start[order_index]:
                        minimum, maximum = maximum, minimum

                    # Merge minimum and maximum into a new line
                    self.lines[dir][new_color].remove(minimum)
                    self.lines[dir][new_color].remove(maximum)

                    new_line = ConsecutiveLine(
                        minimum.start,
                        maximum.end,
                        minimum.start_open_end,
                        maximum.end_open_end,
                        dir,
                        new_color,
                        1+minimum.num_consecutive + maximum.num_consecutive
                    )

                    if minimum.start_open_end:
                        open_dict[minimum.get_open_start()].remove(minimum)
                        open_dict[minimum.get_open_start()].append(new_line)

                    if maximum.end_open_end:
                        open_dict[maximum.get_open_end()].remove(maximum)
                        open_dict[maximum.get_open_end()].append(new_line)

                    open_dict[(x, y)] = []
                    self.lines[dir][new_color].append(new_line)
            else:
                # This point is isolated in this direction, add it anyway
                has_open_start = safe_is_empty(x-dx, y-dy)
                has_open_end = safe_is_empty(x+dx, y+dy)

                if has_open_start or has_open_end:
                    line = ConsecutiveLine((x, y), (x, y), has_open_start, has_open_end, dir, new_color, 1)
                    self.lines[dir][new_color].append(line)

                    open_dict[(x, y)] = []

                    if has_open_start:
                        open_dict[line.get_open_start()] = [line]

                    if has_open_end:
                        open_dict[line.get_open_end()] = [line]

        opposite_color = other_color(new_color)

        # Handle the opposite color
        for dir in DIRS:
            open_dict = self.open_end_dicts[dir][opposite_color]
            if (x, y) in open_dict:
                # The point we are updating is already an end
                lines = open_dict[(x, y)]

                lines_to_delete = [line for line in lines if line.num_open_ends == 1]
                lines = [line for line in lines if line.num_open_ends == 2]

                # Delete all reference to the old line
                for line in lines_to_delete:
                    self.lines[dir][opposite_color].remove(line)
                    # Delete score of old lines
                    self.score[opposite_color] -= line.cached_score

                # Update still remaining lines to reflect that they have one less open end
                for line in lines:
                    line.num_open_ends -= 1
                    if line.is_starting_end(x, y):
                        line.start_open_end = False
                    else:
                        line.end_open_end = False

                open_dict[(x, y)] = []

        self.recalculate_score()

    def recalculate_score(self):
        self.score[BLACK] = 0
        self.score[WHITE] = 0

        for color in COLORS:
            for dir in DIRS:
                for line in self.lines[dir][color]:
                    self.score[color] += line.score(self.simulator.state()[0])

    def check(self):
        grid = self.simulator.state()[1]

        for color in COLORS:
            for dir in DIRS:
                for line in self.lines[dir][color]:
                    line.check(grid)

        # Check open grid
        for color in COLORS:
            for dir in DIRS:
                dx, dy = DIR_TO_DELTA[dir]

                open_dict = self.open_end_dicts[dir][color]

                for (x, y), lines in open_dict.items():
                    if len(lines) > 2:
                        raise ValueError('At most 2 lines could have the same endpoint')

                    if grid[x][y] != EMPTY:
                        raise ValueError('Open end is not EMPTY in grid')

                    for line in lines:
                        if (x, y) == (line.start[0] - dx, line.start[1] - dy):
                            if not line.start_open_end:
                                raise ValueError('Line does not have open start end')
                        elif (x, y) == (line.end[0] + dx, line.end[1] + dy):
                            if not line.end_open_end:
                                raise ValueError('Line does not have open end')
                        else:
                            raise ValueError("Open dict points to line to whom it's not neither start or end point")

    def get_value_for_player(self, color):
        return self.score[color] - self.score[other_color(color)]

class AI:
    # NOTE: modifying this block is not recommended because it affects the random number sequences
    def __init__(self, state):
        self.simulator = Game()
        self.simulator.reset(*state) #using * to unpack the state tuple
        self.root = Node(state, self.simulator.get_actions())

    def mcts_search(self):

        #TODO: Implement the main MCTS loop

        iters = 0
        action_win_rates = {} #store the table of actions and their ucb values

        while(iters < BUDGET):
            #if ((iters + 1) % 100 == 0):
                # NOTE: if your terminal driver doesn't support carriage returns you can use: 
                # print("{}/{}".format(iters + 1, BUDGET))
                #print("\riters/budget: {}/{}".format(iters + 1, BUDGET), end="")

            # TODO: select a node, rollout, and backpropagate
            s = self.select(self.root)
            result = self.rollout(s)
            self.backpropagate(s, result)

            iters += 1
        #print()

        # Note: Return the best action, and the table of actions and their win values 
        #   For that we simply need to use best_child and set c=0 as return values
        _, action, action_win_rates = self.best_child(self.root, 0)

        return action, action_win_rates

    def select(self, node):

        # TODO: select a child node
        # HINT: you can use 'is_terminal' field in the Node class to check if node is terminal node
        # NOTE: deterministic_test() requires using c=1 for best_child()

        while not node.is_terminal:
            if len(node.untried_actions) > 0:
                return self.expand(node)
            else:
                node = self.best_child(node)[0]

        return node

    def expand(self, node):

        # TODO: add a new child node from an untried action and return this new node

        # NOTE: passing the deterministic_test() requires popping an action like this
        action = node.untried_actions.pop(0)

        # NOTE: Make sure to add the new node to node.children
        # NOTE: You may find the following methods useful:
        #   self.simulator.state()
        #   self.simulator.get_actions()
        self.simulator.reset(*node.state)
        self.simulator.place(*action)

        # choose a child node to grow the search tree
        child_node = Node(self.simulator.state(), self.simulator.get_actions(), node)
        node.children.append((action, child_node))

        return child_node

    def best_child(self, node, c=1):

        # TODO: determine the best child and action by applying the UCB formula

        best_child_node = None # to store the child node with best UCB
        best_action = None # to store the action that leads to the best child
        best_ucb = -math.inf
        action_ucb_table = {} # to store the UCB values of each child node (for testing)

        N_n = node.num_visits

        # NOTE: deterministic_test() requires iterating in this order
        for action, child in node.children:
            # NOTE: deterministic_test() requires, in the case of a tie, choosing the FIRST action with 
            # the maximum upper confidence bound 
            Q_c = child.num_wins
            N_c = child.num_visits

            node_quality = Q_c / N_c + child.heuristic.get_value_for_player(node.state[0]) / (10 * (N_c + 1))
            ucb = node_quality + c * sqrt( (2 * log(N_n)) / N_c )

            action_ucb_table[action] = ucb

            if ucb > best_ucb:
                best_child_node = child
                best_action = action
                best_ucb = ucb

        return best_child_node, best_action, action_ucb_table

    def backpropagate(self, node, result):

        def delta(s):
            return result[s.state[0]]

        while node is not None:
            # TODO: backpropagate the information about winner
            # IMPORTANT: each node should store the number of wins for the player of its **parent** node
            node.num_visits += 1

            if node.parent is not None:
                node.num_wins += delta(node.parent)

            node = node.parent

    def rollout(self, node):

        # TODO: rollout (called DefaultPolicy in the slides)

        # HINT: you may find the following methods useful:
        #   self.simulator.reset(*node.state)
        #   self.simulator.game_over
        #   self.simulator.rand_move()
        #   self.simulator.place(r, c)
        # NOTE: deterministic_test() requires that you select a random move using self.simulator.rand_move()

        self.simulator.reset(*node.state)


        # TODO: Use heuristics for a 1-level min-max tree + forced attacks / defenses
        while not self.simulator.game_over:
            action = self.simulator.rand_move()
            self.simulator.place(*action)

        # Determine reward indicator from result of rollout
        reward = {}
        if self.simulator.winner == BLACK:
            reward[BLACK] = 1
            reward[WHITE] = 0
        elif self.simulator.winner == WHITE:
            reward[BLACK] = 0
            reward[WHITE] = 1
        return reward
