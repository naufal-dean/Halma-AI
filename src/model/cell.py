from enum import IntEnum
from player import Player


class CellType(IntEnum):
    NEUTRAL = 0
    RED_HOUSE = 1
    GREEN_HOUSE = 2

class Pion(IntEnum):
    NONE = 0
    RED = 1
    GREEN = 2

class Cell:
    def __init__(self, owner, pion, row, col):
        self.owner = owner
        self.pion = pion
        self.row = row
        self.col = col

    def check(self, cell, id):
        return self.pion == Pion.NONE and not (
            cell.owner == CellType.NEUTRAL and self.owner == id or cell.owner != CellType.NEUTRAL and cell.owner != id and self.owner != cell.owner
        )
    def set_pion(self, pion):
        self.pion = pion

    def occupied_by(self, player: Player):
        if player == Player.RED:
            return self.pion == Pion.RED
        elif player == Player.GREEN:
            return self.pion == Pion.GREEN
        else:
            return False
