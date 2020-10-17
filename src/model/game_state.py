from .halma import Board
from .cell import Pion
from .player import Player


class GameState:
    def __init__(self, board: Board, hum_player: Player, act_player: Player = Player.RED):
        self.board = board
        self.hum_player = hum_player
        self.act_player = act_player

    def next_turn(self):
        self.act_player = Player.RED if self.act_player == Player.GREEN else Player.GREEN

    def is_red_player_win(self):
        offset = 0
        for sum in range(self.board.size + (self.board.size // 2) - 2 + 1, (self.board.size - 1) * 2 + 1):
            for i in range((self.board.size // 2) + offset, self.board.size):
                if self.board[i, sum-i].pion != Pion.RED:
                    return False
            offset += 1
        return True

    def is_green_player_win(self):
        for sum in range(0, self.board.size // 2):
            for i in range(0, sum + 1):
                if self.board[i, sum-i].pion != Pion.GREEN:
                    return False
        return True

    def check_winner(self):
        if self.is_red_player_win():
            return Player.RED
        elif self.is_green_player_win():
            return Player.GREEN
        else:
            return None
