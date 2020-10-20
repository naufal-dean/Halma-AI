from collections import deque
from .cell import Cell, CellType, Pion
from .player import Player
import math, sys, time, random
import numpy as np

class Board:
    def __init__(self, size, max_depth=1, max_time=-1, prune=True):
        assert(size & 1 == 0)
        self.max_depth = max_depth
        self.max_time = max_time
        self.prune = False
        self.timer = 0
        self.cost = 0
        self.size = size
        self.count_finish_red = 0
        self.count_finish_green = 0
        self.gen_board()
        self.set_count_pion()
        self.child = 0 # Debug

    def load_from_file(self, filename):
        d = open(filename, "r").read().split("\n")[:self.size]
        assert(len(d) == self.size)
        for i in range(len(d)):
            a = d[i].split(" | ")
            for j in range(len(a)):
                self.cells[i][j].pion = int(a[j])

    def __getitem__(self, index):
        try:
            return self.cells[index[0], index[1]]
        except Exception:
            return None

    def gen_board(self):
        self.cells = np.empty((self.size, self.size), dtype=Cell)
        for i in range(self.size):
            # Contraint number
            d_size = self.size//2
            c = (d_size-i-1) % self.size
            # Gen row
            for j in range(self.size):
                owner = CellType.NEUTRAL
                # Top-left side
                if c < d_size and j <= c:
                    owner = CellType.RED_HOUSE
                # Bottom-right side
                elif c >= d_size and j >= c:
                    owner = CellType.GREEN_HOUSE
                self.cells[i, j] = Cell(owner, owner, i, j)

    def set_count_pion(self):
        self.count_pion = 0
        for i in range(self.size//2, 0, -1):
            self.count_pion += i

    def go_everywhere(self, cell: Cell, possible_steps, s, original: Cell, id: int):
        steps = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]
        # Try all move (left, right, up, down, etc..)
        for step in steps:
            row = cell.row + step[0]
            col = cell.col + step[1]
            # If feasible
            if row >= 0 and col >= 0 and row < self.size and col < self.size:
                # Is it emptpy to put the pion?
                if self[row, col].pion == Pion.NONE:
                    # Do not repeat same move and do not put to stack
                    if cell == original and self[row, col].check(original, id) and (original, self[row, col]) not in possible_steps:
                        possible_steps.append((original, self[row, col]))
                else: # Try jump/skip to next empty cell
                    row = cell.row + step[0]*2
                    col = cell.col + step[1]*2
                    # If feasible
                    if row >= 0 and col >= 0 and row < self.size and col < self.size:
                        # Check empty and do not repeat same move
                        if self[row, col].check(original, id) and (original, self[row, col]) not in possible_steps:
                            possible_steps.append((original, self[row, col]))
                            s.append(self[row, col])

    def dfs_path(self, row: int, col: int, id: int):
        possible_steps = []
        s = deque()
        original = self[row, col]
        s.append(original)
        while s:
            cell = s.pop()
            self.go_everywhere(cell, possible_steps, s, original, id)
        return possible_steps

    def gen_all_pos_steps(self, id: int):
        possible_steps = deque()
        for row in range(self.size):
            for col in range(self.size):
                if self[row, col].pion == id:
                    possible_steps.extend(self.dfs_path(row, col, id))
        return possible_steps

    def apply_step(self, step: tuple):
        # Pre-condition: step[0].pion != Pion.NONE and step[1].pion == Pion.NONE
        # Win condition update + cost update
        if step[0].pion == Pion.RED:
            self.cost -= (self.size - step[0].row -1) + (self.size - step[0].col -1)
            self.cost += (self.size - step[1].row -1) + (self.size - step[1].col -1)
            self.count_finish_red += step[0].owner != CellType.GREEN_HOUSE and step[1].owner == CellType.GREEN_HOUSE
        elif step[0].pion == Pion.GREEN:
            self.cost += step[0].row + step[0].col
            self.cost -= step[1].row + step[1].col
            self.count_finish_green += step[0].owner != CellType.RED_HOUSE and step[1].owner == CellType.RED_HOUSE
        # Apply step
        step[1].pion = step[0].pion
        step[0].pion = Pion.NONE

    def undo_step(self, step: tuple):
        # Pre-condition: step[0].pion == Pion.NONE and step[1].pion != Pion.NONE
        # Win condition update + cost update
        if step[1].pion == Pion.RED:
            self.cost += (self.size - step[0].row -1) + (self.size - step[0].col -1)
            self.cost -= (self.size - step[1].row -1) + (self.size - step[1].col -1)
            self.count_finish_red -= step[0].owner != CellType.GREEN_HOUSE and step[1].owner == CellType.GREEN_HOUSE
        elif step[1].pion == Pion.GREEN:
            self.cost -= step[0].row + step[0].col
            self.cost += step[1].row + step[1].col
            self.count_finish_green -= step[0].owner != CellType.RED_HOUSE and step[1].owner == CellType.RED_HOUSE
        # Undo step
        step[0].pion = step[1].pion
        step[1].pion = Pion.NONE


    def terminal_test(self, depth: int, id: int, maxing: bool):
        delta = time.time() - self.timer
        # Constraint check
        if depth == self.max_depth or self.max_time != -1 and delta > self.max_time:
            return None
        # Switch player
        if not maxing:
            id = (id % 2) + 1
        # Win check
        if self.count_finish_green == self.count_pion or self.count_finish_red == self.count_pion:
            return None
        # Generate possible steps with DFS
        steps = self.gen_all_pos_steps(id)
        if not steps:
            return None
        return steps

    def init_step_cost(self, maxing: bool):
        # Init step cost for max & min condition
        if maxing:
            return (-sys.maxsize, None)
        else:
            return (sys.maxsize, None)

    def optimize_step_cost(self, maxing: bool, osc1: tuple, osc2: tuple):
        # Use random here for better performance
        if maxing:
            return osc1 if osc1[0] > osc2[0] or osc1[0] == osc2[0] and random.randint(1,2) == 1 else osc2
        else:
            return osc1 if osc1[0] < osc2[0] or osc1[0] == osc2[0] and random.randint(1,2) == 1 else osc2

    def objective_function(self, id: int):
        # Use pre-compute cost (more cheap)
        total = self.cost
        if id == Pion.RED:
            total *= -1
        return total

    def legal_moves(self, row: int, col: int, id: int):
        return self.dfs_path(row, col, id)

    # minimax algorithm
    def minimax(self, id: int):
        self.max_depth = 3
        self.timer = time.time()
        self.child = 0
        return self.minimax_rec(id, True, 0, None, -sys.maxsize, sys.maxsize)

    def minimax_rec(self, id: int, maxing: bool, depth: int, step: tuple, a: int, b: int):
        self.child += 1
        steps = self.terminal_test(depth, id, maxing)
        if steps is None:
            return (self.objective_function(id), step)

        opt_step_cost = self.init_step_cost(maxing)
        while steps:
            step = steps.pop()
            self.apply_step(step)

            # Apply minimax to current state
            res = self.minimax_rec(id, not maxing, depth+1, step, a, b)
            opt_step_cost = self.optimize_step_cost(maxing, opt_step_cost, (res[0], step))

            self.undo_step(step)
            # Pruning
            if self.prune:
                if maxing:
                    a = a if a >= res[0] else res[0]
                else:
                    b = b if b <= res[0] else res[0]

                if a >= b:
                    break
        return opt_step_cost

    # minimax_with_local algorithm (local search using simulated annealing)
    # sample_div: max loop in each minimax level == max(sample_min, len(steps) // sample_div)
    def minimax_with_local(self, id: int, anneal_threshold: float = 0.8,
                           sample_min: int = 25, sample_div: float = 1.5):
        assert 0 <= anneal_threshold <= 1
        self.max_depth = 3
        self.timer = time.time()
        self.child = 0
        return self.minimax_with_local_rec(id, True, 0, None, -sys.maxsize, sys.maxsize)



    def minimax_with_local_rec(self, id: int, maxing: bool, depth: int, step: tuple, a: int, b: int):
        self.child += 1
        parent_a = self.terminal_test(depth, id, maxing)
        if parent_a is None:
            return (self.objective_function(id), parent_a)
        parent_b = self.terminal_test(depth, id, not maxing)
        if parent_b is None:
            return (self.objective_function(id), parent_b)
        offspring = deque()
        for i in range(len(parent_a) if len(parent_a) <= len(parent_b) else len(parent_b)):
            if parent_a:
                offspring.append(parent_a.pop())
            if parent_b:
                offspring.append(parent_b.pop())
        steps = offspring


        opt_step_cost = self.init_step_cost(maxing)
        while steps:
            step = steps.pop()
            self.apply_step(step)

            # Apply minimax_with_local to current state
            res = self.minimax_with_local_rec(id, not maxing, depth+1, step, a, b)
            opt_step_cost = (res[0], step)
            self.undo_step(step)
            # Pruning
            if self.prune:
                if maxing:
                    a = a if a >= res[0] else res[0]
                else:
                    b = b if b <= res[0] else res[0]

                if a >= b:
                    break
        return opt_step_cost

    # Debug
    def play(self):
        try:
            for i in range(1000):
                x = time.time()
                step = self.minimax(1)[1]
                self.apply_step(step)
                print(self.child, time.time()-x)
                # self.print_matrix()
                step = self.minimax(2)[1]
                self.apply_step(step)
                print(self.child, time.time()-x)
                # self.print_matrix()
        except Exception as e:
            print(e)
            print("Game finished")

    # Debug
    def print_matrix(self):
        for i in range(self.size):
            for j in range(self.size-1):
                print(int(self[i, j].pion), end=" | ")
            print(int(self[i, -1].pion))
        print()

if __name__ == "__main__":
    board = Board(16, max_depth=2, max_time=-1, prune=True)
    # board.load_from_file("test.txt")
    board.print_matrix()
    board.play()
    board.print_matrix()
