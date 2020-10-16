from .board import Board
from .player import Player


class GameState:
    def __init__(self, board: Board, hum_player: Player, act_player: Player = Player.RED):
        self.board = board
        self.hum_player = hum_player
        self.act_player = act_player

    def next_turn(self):
        self.act_player = Player.RED if self.act_player == Player.GREEN else Player.GREEN
