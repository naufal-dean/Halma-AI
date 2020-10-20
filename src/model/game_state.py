from controller.halma import Board
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
        if self.board.count_finish_red == self.board.count_pion:
            return True
        return False

    def is_green_player_win(self):
        if self.board.count_finish_green == self.board.count_pion:
            return True
        return False

    def check_winner(self):
        if self.is_red_player_win():
            return Player.RED
        elif self.is_green_player_win():
            return Player.GREEN
        else:
            return None
