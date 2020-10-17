from collections import deque
from .cell import Cell, CellType, Pion
from .player import Player
import sys, time, random

class Board:
    def __init__(self, size, max_depth=-1, max_time=-1, prune=False):
        assert(size & 1 == 0)
        self.max_depth = max_depth
        self.max_time = max_time
        self.prune = False
        self.timer = 0
        self.size = size
        self.gen_board()
        self.child = 0 # Debug

    def load_from_file(self, filename):
        d = open(filename, "r").read().split("\n")
        assert(len(d) == self.size)
        for i in range(len(d)):
            a = d[i].split(" | ")
            for j in range(len(a)):
                self.cells[i][j].pion = int(a[j])

    def __getitem__(self, index):
        try:
            return self.cells[index[0]][index[1]]
        except Exception:
            return None

    def gen_board(self):
        self.cells = []
        for i in range(self.size):
            temp = []

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
                temp.append(Cell(owner, owner, i, j))
            self.cells.append(temp)

    def go_everywhere(self, cell: Cell, possible_steps, s, original: Cell, id: int):
        steps = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]
        for step in steps:
            row = cell.row + step[0]
            col = cell.col + step[1]
            # print(row, col)
            if row >= 0 and col >= 0 and row < self.size and col < self.size:
                if self[row, col].pion == Pion.NONE:
                    if cell == original and self[row, col].check(original, id) and (original, self[row, col]) not in possible_steps:
                        possible_steps.append((original, self[row, col]))
                else:
                    row = cell.row + step[0]*2
                    col = cell.col + step[1]*2
                    if row >= 0 and col >= 0 and row < self.size and col < self.size:
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
        step[1].pion = step[0].pion
        step[0].pion = Pion.NONE

    def undo_step(self, step: tuple):
        step[0].pion = step[1].pion
        step[1].pion = Pion.NONE

    def terminal_test(self, depth: int, id: int, maxing: bool):
        delta = time.time() - self.timer
        if depth == self.max_depth or self.max_time != -1 and delta > self.max_time:
            return None
        if not maxing:
            id = (id % 2) + 1
        win = True
        if id == Player.GREEN:
            for i in range(self.size//2, self.size):
                for j in range(self.size*3//2-i-1, self.size):
                    win = self[i, j].pion == (id % 2) + 1
                    if not win:
                        break
                if not win:
                    break
        else:
            for i in range(self.size//2):
                for j in range(self.size//2-i):
                    win = self[i, j].pion == (id % 2) + 1
                    if not win:
                        break
                if not win:
                    break
        if win:
            return None
        steps = self.gen_all_pos_steps(id)
        if not steps:
            return None
        return steps

    def minimax(self, id: int):
        self.timer = time.time()
        self.child = 0
        return self.minimax_rec(id, True, 0, None, -sys.maxsize, sys.maxsize)

    def init_step_cost(self, maxing: bool):
        if maxing:
            return (-sys.maxsize, None)
        else:
            return (sys.maxsize, None)

    def optimize_step_cost(self, maxing: bool, osc1: tuple, osc2: tuple):
        if maxing:
            return osc1 if osc1[0] > osc2[0] or osc1[0] == osc2[0] and random.randint(1,2) == 1 else osc2
        else:
            return osc1 if osc1[0] < osc2[0] or osc1[0] == osc2[0] and random.randint(1,2) == 1 else osc2

    def objective_function(self, id: int):
        total = [0, 0]
        for row in range(self.size):
            for col in range(self.size):
                if self[row, col].pion == Pion.RED:
                    # if self[row, col].owner == (id%2)+1:
                    #     total[0] -= 5
                    # else:
                        total[0] += (self.size-row-1) + (self.size-col-1)
                        # temp = self.size**2
                        # for i in range(self.size//2, self.size):
                        #     for j in range(self.size//2+i-1, self.size):
                        #         if self[i, j].pion == 0:
                        #             temp = min(temp, abs(i-row-1) + abs(j-col-1))
                        # total[0] += temp
                elif self[row, col].pion == Pion.GREEN:
                    total[1] += row + col
        return - total[id-1] + total[(id%2)]

    def minimax_rec(self, id: int, maxing: bool, depth: int, step: tuple, a: int, b: int):
        self.child += 1
        steps = self.terminal_test(depth, id, maxing)
        if steps is None:
            return (self.objective_function(id), step)

        opt_step_cost = self.init_step_cost(maxing)
        while steps:
            step = steps.pop()
            self.apply_step(step)
            res = self.minimax_rec(id, maxing, depth+1, step, a, b)
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

    def legal_moves(self, row: int, col: int, id: int):
        print(self.dfs_path(row, col, id))
        return self.dfs_path(row, col, id)

    def play(self):
        try:
            for i in range(1000):
                step = self.minimax(1)[1]
                self.apply_step(step)
                print(step[0].row, step[0].col, step[1].row, step[1].col)
                print(self.objective_function(1))
                # print(self.child)
                self.print_matrix()
                step = self.minimax(2)[1]
                self.apply_step(step)
                print(self.objective_function(2))
                print(step[0].row, step[0].col, step[1].row, step[1].col)
                self.print_matrix()
        except Exception:
            print("Game finished")

    def print_matrix(self):
        for i in range(self.size):
            for j in range(self.size-1):
                print(int(self[i, j].pion), end=" | ")
            print(int(self[i, -1].pion))

if __name__ == "__main__":
    board = Board(16, max_depth=1, max_time=1, prune=True)
    # board.load_from_file("src/model/bad.txt")
    board.print_matrix()
    board.play()
    board.print_matrix()
