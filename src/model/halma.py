from collections import deque
from functools import lru_cache
import sys, time, random
import hashlib

class Player:
    def __init__(self, id):
        self.id = id

class Lane:
    def __init__(self, owner, content, row, col):
        self.owner = owner
        self.content = content
        self.row = row
        self.col = col

    def __str__(self):
        return str(self.content)

    def check(self, lane, id):
        return self.content == 0 and not (lane.owner == 0 and self.owner == id or lane.owner != 0 and lane.owner != id and self.owner != lane.owner)

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

    def __hash__(self):
        acc = ""
        for i in self.matrix:
            acc += "".join(str(x) for x in i)
        return int(hashlib.md5(acc.encode("utf-8")).hexdigest(), 16)

    def load_from_file(self, filename):
        d = open(filename, "r").read().split("\n")
        assert(len(d) == self.size)
        for i in range(len(d)):
            a = d[i].split(" | ")
            for j in range(len(a)):
                self.matrix[i][j].content = int(a[j])

    def __getitem__(self, index):
        try:
            return self.matrix[index[0]][index[1]]
        except Exception:
            return None

    def gen_board(self):
        self.matrix = []
        for i in range(self.size):
            temp = []

            # Contraint number
            d_size = self.size//2
            c = (d_size-i-1) % self.size

            # Gen row
            for j in range(self.size):
                owner = 0
                # Top-left side
                if c < d_size and j <= c:
                    owner = 1
                # Bottom-right side
                elif c >= d_size and j >= c:
                    owner = 2
                temp.append(Lane(owner, owner, i, j))
            self.matrix.append(temp)

    def go_everywhere(self, lane, possible_steps, s, original, id):
        steps = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]
        for step in steps:
            row = lane.row + step[0]
            col = lane.col + step[1]
            # print(row, col)
            if row >= 0 and col >= 0 and row < self.size and col < self.size:
                if self[row, col].content == 0:
                    # print(self[row, col], original)
                    # print(self[row, col] != original)
                    if lane == original and self[row, col].check(original, id) and (original, self[row, col]) not in possible_steps:
                        # print("o")
                        possible_steps.append((original, self[row, col]))
                else:
                    row = lane.row + step[0]*2
                    col = lane.col + step[1]*2
                    if row >= 0 and col >= 0 and row < self.size and col < self.size:
                        if self[row, col].check(original, id) and (original, self[row, col]) not in possible_steps:
                            possible_steps.append((original, self[row, col]))
                            s.append(self[row, col])

    def dfs_path(self, row, col, id):
        possible_steps = []
        s = deque()
        original = self[row, col]
        s.append(original)
        while s:
            lane = s.pop()
            # print(lane.row, lane.col)
            self.go_everywhere(lane, possible_steps, s, original, id)
        return possible_steps

    def gen_all_pos_steps(self, id):
        possible_steps = deque()
        for row in range(self.size):
            for col in range(self.size):
                if self[row, col].content == id:
                    possible_steps.extend(self.dfs_path(row, col, id))
        return possible_steps

    def apply_step(self, step):
        step[1].content = step[0].content
        step[0].content = 0

    def undo_step(self, step):
        step[0].content = step[1].content
        step[1].content = 0

    def terminal_test(self, depth, id, maxing):
        delta = time.time() - self.timer
        if depth == self.max_depth or self.max_time != -1 and delta > self.max_time:
            return None
        if not maxing:
            id = (id % 2) + 1
        win = True
        if id == 2:
            for i in range(self.size//2, self.size):
                for j in range(self.size*3//2-i-1, self.size):
                    win = self[i, j].content == (id % 2) + 1
                    if not win:
                        break
                if not win:
                    break
        else:
            for i in range(self.size//2):
                for j in range(self.size//2-i):
                    win = self[i, j].content == (id % 2) + 1
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

    def minimax(self, id):
        self.timer = time.time()
        self.child = 0
        dp = {}
        return self.minimax_rec(id, True, 0, None, -sys.maxsize, sys.maxsize, dp)

    def init_step_cost(self, maxing):
        if maxing:
            return (-sys.maxsize, None)
        else:
            return (sys.maxsize, None)

    def optimize_step_cost(self, maxing, osc1, osc2):
        if maxing:
            return osc1 if osc1[0] > osc2[0] or osc1[0] == osc2[0] and random.randint(1,5) == 1 else osc2
        else:
            return osc1 if osc1[0] < osc2[0] or osc1[0] == osc2[0] and random.randint(1,5) == 1 else osc2

    def objective_function(self, id):
        total = [0, 0]
        for row in range(self.size):
            for col in range(self.size):
                if self[row, col].content == 1:
                    # if self[row, col].owner == (id%2)+1:
                    #     total[0] -= 5
                    # else:
                        total[0] += (self.size-row-1) + (self.size-col-1)
                        # temp = self.size**2
                        # for i in range(self.size//2, self.size):
                        #     for j in range(self.size//2+i-1, self.size):
                        #         if self[i, j].content == 0:
                        #             temp = min(temp, abs(i-row-1) + abs(j-col-1))
                        # total[0] += temp
                elif self[row, col].content == 2:
                    total[1] += row + col
        return - total[id-1] + total[(id%2)]

    def minimax_rec(self, id, maxing, depth, step, a, b, dp):
        # state = hash(self)
        # if dp.get(state, None):
        #     return dp[state]
        self.child += 1
        steps = self.terminal_test(depth, id, maxing)
        if steps is None:
            return (self.objective_function(id), step)

        opt_step_cost = self.init_step_cost(maxing)
        while steps:
            step = steps.pop()
            self.apply_step(step)
            res = self.minimax_rec(id, maxing, depth+1, step, a, b, dp)
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
        # dp[state] = opt_step_cost
        return opt_step_cost

    def play(self):
        try:
            for i in range(100):
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
        except Exception as e:
            print(e)
            print("Game finished")

    # def minimax(self, id):
    #     commit_stack = deque()
    #     rollback_stack = deque()
    #     steps = self.terminal_test(0, id)
    #     if steps is None:
    #         raise Exception("Why are you doing this?")
    #     # State: [steps, maxing, depth]
    #     commit_stack.append([steps, True, 0])

    #     while not commit_stack.empty():
    #         state = commit_stack.pop()
    #         if state[0]:
    #             step = state[0].pop()
    #             self.apply_step(step)

    #             # Terminal test
    #             steps = self.terminal_test(0, id)
    #             if steps is None:
    #                 return 1

    #             revstate = deque()
    #             revstate.append(step)
    #             rollback_stack.append(revstate)
    #         else:
    #             revstate = rollback_stack.pop()

    def print_matrix(self):
        for i in range(self.size):
            for j in range(self.size-1):
                print(self.matrix[i][j].content, end=" | ")
            print(self.matrix[i][-1].content)

if __name__ == "__main__":
    board = Board(8, max_depth=2, max_time=0.2, prune=True)
    board.print_matrix()
    # temp = board.gen_all_pos_steps(1)
    # temp = board.dfs_path(0,0)
    # print("")
    # for i in temp:
    #     print(i[1].row, i[1].col)
    board.play()
    board.print_matrix()
    # start = time.time()
    # res = board.minimax(1)
    # print(time.time()-start)
    # print(board.child)
    # print(res)
    # print(res[1][0].row, res[1][0].col, res[1][1].row, res[1][1].col)