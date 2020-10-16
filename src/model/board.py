from .cell import Cell, CellType, Pion
# from cell import Cell, CellType, Pion


class Board:
    def __init__(self, size=16):
        assert size in [8, 10, 16]
        self.size = size
        self.init_cells()

    def init_cells(self):
        self.cells = []
        for r in range(self.size):
            row = []
            for c in range(self.size):
                # check cell type, and initial pion
                if (r + c) < (self.size // 2):
                    cell_type = CellType.RED_HOUSE
                    pion = Pion.RED
                elif (r + c) > (self.size + (self.size // 2) - 2):
                    cell_type = CellType.GREEN_HOUSE
                    pion = Pion.GREEN
                else:
                    cell_type = CellType.NEUTRAL
                    pion = Pion.NONE
                # append
                row.append(Cell(cell_type, pion))
            self.cells.append(row)

    def move(self, src: tuple, dst: tuple):
        # assume src and dst is valid, use legal_moves to check valid move
        # or check if dst in self.legal_moves(src), but duplicate calculation
        self.cells[dst[0]][dst[1]].set_pion(self.cells[src[0]][src[1]].pion)
        self.cells[src[0]][src[1]].set_pion(Pion.NONE)

    def legal_moves(self, src: tuple):
        return [(8,7), (8,8), (8,9)]


if __name__ == '__main__':
    b = Board()
    print(b.cells[0][0].pion, b.cells[0][0].cell_type)
    print(b.cells[8][8].pion, b.cells[8][8].cell_type)
    b.move((0,0), (8,8))
    print(b.cells[0][0].pion, b.cells[0][0].cell_type)
    print(b.cells[8][8].pion, b.cells[8][8].cell_type)
