from enum import IntEnum

from .player import Player


class CellType(IntEnum):
    RED_HOUSE = 0
    GREEN_HOUSE = 1
    NEUTRAL = 2


class Pion(IntEnum):
    RED = 0
    GREEN = 1
    NONE = 2


class Cell:
    def __init__(self, cell_type: CellType, pion: Pion):
        self.cell_type = cell_type
        self.pion = pion

    def set_pion(self, pion):
        self.pion = pion

    def occupied_by(self, player: Player):
        if player == Player.RED:
            return self.pion == Pion.RED
        elif player == Player.GREEN:
            return self.pion == Pion.GREEN
        else:
            return False
